import pysftp
import xml.etree.ElementTree as ET
import json
import requests, math, pytz
from collections import defaultdict
from bodega.models import File, PurchaseOrder, Ingredient, Product
from bodega.helpers.utils import logger
from bodega.helpers.oc_functions import getOc, receiveOc
from bodega.helpers.bodega_functions import *
from bodega.constants.config import ocURL, almacenes
from .utils import hashQuery
from bodega.constants.logic_constants import *
from bodega.helpers.functions import *
from django.utils import timezone


def send_to_profe(oc): # Esta funcion debiera ser llamada con esa libreria que programa la ejecucion
    stock_almacen, stock = get_inventory()
    for almacen in stock_almacen:
        if oc.sku in stock_almacen[almacen]: # Vemos si el sushi esta en el almacen
            products = get_products_with_sku(almacenes[almacen], oc.sku)
            count = 0
            ready = False
            for product in products:
                send_product(product['_id'], oc.oc_id, 'CualquierDireccion', oc.price)
                count += 1
                if count >= oc.amount:
                    ready = True
                    break
            if ready: # Si se completo la order, no revisamos mas almacenes
                break


def finish_oc(oc):
    products = get_products_with_sku(almacenes['cocina'], oc.sku)
    i = oc.sended
    if oc.sended < oc.amount:
        for product in products[:(oc.amount-i)]:
            response = send_product(product['_id'], oc.oc_id, 'CualquierDireccion', oc.price)
            i+=1
            oc.sended=i
            oc.save()
        
        if oc.sended >= oc.amount:
            oc.state='finalizada'
            oc.save()
    else:
        oc.state='finalizada'
        oc.save()



def check_not_finished():
    not_finished_ocs = PurchaseOrder.objects.filter(state='iniciada', channel='ftp', deadline__gte=timezone.now()).order_by('created_at')
    if not_finished_ocs:
        stock_almacenes, stock = get_inventory()
        for oc in not_finished_ocs:
            stock_actual = stock_almacenes['cocina'].get(str(oc.sku), 0)
            if stock_actual > 0:
                finish_oc(oc)


def check_not_initiated():
    """
    Revisa las ocs que no esten finished y las recorre llamando a try_to_produce_highlevel
    para intentar producir los productos de nivel 10k, 20k y 30k.
    """
    not_iniciated_ocs = PurchaseOrder.objects.filter(state='creada', channel='ftp').order_by('created_at') # Filtramos las ocs que no han sido atendidas aun
    if not_iniciated_ocs:
        _, stock = get_inventory()
        for oc in not_iniciated_ocs:
            if oc.deadline < timezone.now():
                oc.delete()
            else:
                ingredients = Ingredient.objects.filter(sku_product=oc.sku) # Obtenemos que ingredientes necesita
                all_in_stock = True # Partimos asumiendo que tenemos todos los ingredientes en stock
                space = 0
                los_que_faltan = []
                for ing in ingredients:
                    quantity = oc.amount * ing.volume_in_store
                    real_stock = stock.get(str(ing.sku_ingredient.sku), 0)
                    if real_stock < quantity: # Si no tenemos lo suficiente mandamos a producir del ingrediente
                        all_in_stock = False
                        los_que_faltan.append(ing.sku_ingredient.sku) # Con esto se espera que la proxima vez que reisemos esta oc, ya tengamos este ingrediente en stock
                    else:
                        space += quantity

                if all_in_stock:
                    # Si tenemos todos los ingredientes, hacemos espacio en cocina y los enviamos a cocina para producir... Si no, esperamos que en la siguiente ejecucion ya los tengamos todos
                    space_available = check_space(space, 'cocina')
                    if not space_available:
                        make_space_in_almacen("cocina", random.choice(['libre1', 'libre2']), space)
                    for ing in ingredients:
                        quantity = oc.amount * ing.volume_in_store
                        send_to_somewhere(str(ing.sku_ingredient.sku), quantity, almacenes["cocina"])
                    response = make_a_product(oc.sku, oc.amount)
                    response = receiveOc(oc.oc_id)
                    oc.state='iniciada'
                    oc.save()

                else:
                    create_middle_products(los_que_faltan)


def watch_server():
    """
    Revisa el servidor FTP y actualiza la BD con los archivos nuevos
    no revisados, crea sus correspondientes OC como no finalizadas.
    """
    HOST_NAME = 'fierro.ing.puc.cl'
    USER_NAME = 'grupo9'
    USER_PASSWORD = 'GMChbrR2Y6mFzacu5'
    HOST_PORT = 22
    conn_opts = pysftp.CnOpts()
    conn_opts.hostkeys = None
    with pysftp.Connection(host=HOST_NAME, username=USER_NAME, password=USER_PASSWORD, port=HOST_PORT, cnopts=conn_opts) as sftp:
        print("Conexión establecida con servidor STFP!")
        sftp.cwd('/pedidos')
        dir_structure = sftp.listdir_attr()
        for attr in dir_structure:
            with sftp.open(attr.filename) as archivo:
                file_entity = File.objects.filter(filename=attr.filename)
                must_process = False
                if not file_entity:
                    must_process = True
                tree = ET.parse(archivo)
                root = tree.getroot()
                if must_process:
                    for node in root:
                        if node.tag == 'id':
                            oc_id = node.text
                            raw_response = getOc(oc_id)
                            if raw_response:
                                response = raw_response[0]
                                deadline = response["fechaEntrega"].replace("T", " ").replace("Z","")
                                deadline = datetime.datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.UTC)
                                if deadline > timezone.now():
                                    file_entity, file_created = File.objects.get_or_create(filename=attr.filename,
                                                            processed=True,
                                                            attended=False)
                                    new_oc, oc_created = PurchaseOrder.objects.get_or_create(oc_id=response["_id"], sku=response['sku'], 
                                                                        client=response['cliente'], provider=response['proveedor'],
                                                                        amount=response['cantidad'], price=response["precioUnitario"],
                                                                        channel=response['canal'], deadline=deadline)

    