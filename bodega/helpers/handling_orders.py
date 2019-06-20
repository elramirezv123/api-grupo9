import pysftp
import xml.etree.ElementTree as ET
import json
import requests
from bodega.models import File, PurchaseOrder, Ingredient
from bodega.helpers.oc_functions import getOc, receiveOc
from bodega.helpers.bodega_functions import *
from bodega.constants.config import ocURL, almacenes
from .utils import hashQuery
from bodega.constants.logic_constants import *
from bodega.helpers.functions import *



def try_to_produce_highlevel(sku, amount, sku_inventory, almacen_inventory):
    # Los ingredientes del sku
    ingredients = Ingredient.objects.filter(sku_product_id=sku)
    # Un diccionario de la forma {<sku_ingrediente>: <cantidad_necesaria>}
    ing_with_amount_to_produce = {str(ing.sku_ingredient_id): ing.volume_in_store*amount for ing in ingredients}
    # Diccionario para chequear si tenemos de todo.
    # Es de la forma {<sku_ingrediente>: <cantidad_que_falta>}
    we_need = {sku: amount for sku, amount in ing_with_amount_to_produce.items()}

    needed_skus = [ing.sku_ingredient_id for ing in ingredients]

    #### DEBUG ####
    # print("Para producir {} de {}".format(sku, amount))
    # for ing, ing_amount in ing_with_amount_to_produce.items():
    #     print("Se necesitan {} de {}".format(ing_amount, ing))
    
    # Recorremos nuestros stock de cada sku

    for sku, stock in sku_inventory.items():

        # Si es que el sku es requerido
        if int(sku) in needed_skus:

            # Tenemos este sku en stock. Revisamos si tenemos la cantidad necesaria
            # print("Tenemos {} de {} y se necesita {}".format(stock, sku, ing_with_amount_to_produce[sku]))

            if stock >= ing_with_amount_to_produce[sku]:
                we_need[sku] = 0
            else: 
                we_need[sku] = we_need[sku] - stock
    # Revisamos el diccionario a ver si tenemos de todo

    if check_if_need_something(we_need):
        print("Tenemos de todo!")
    #     kitchen_space_needed = sum([ amount for _, amount in ing_with_amount_to_produce.items()])
    #     # Hacemos el espacio en la cocina
    #     make_space_in_almacen('cocina', "libre1", kitchen_space_needed + 5)
    #     # Movemos los ingredientes a la cocina
    #     for sku, amount in ing_with_amount_to_produce:
    #         send_to_somewhere(sku, amount, almacenes['cocina'])
    #     # Producimos!
    #     make_a_product()
    else:
        print('No tenemos de todo :(')
        print("Nos falta: ")
        for sku, needed_amount in we_need.items():
            if needed_amount > 0:
                print("{} de {}".format(needed_amount, sku))
        


def check_not_finished():
    """
    Revisa las ocs que no esten finished y las recorre llamando a try_to_produce_highlevel
    para intentar producir los productos de nivel 10k, 20k y 30k.
    """
    not_finished_ocs = PurchaseOrder.objects.filter(finished=False)
    if not_finished_ocs:
        stock_almacen, stock = get_inventory()
        almacen_skus = { almacen: list(obj.keys()) for almacen, obj in stock_almacen.items()}
        for oc in not_finished_ocs:
            try:
                sku_stock = int(stock[oc.sku])
            except:
                continue
            if sku_stock >= oc.amount:
                # print("tenemos!")
                almacen_name = None
                for almacen, skus in almacen_skus.items():
                    if str(oc.sku) in skus:
                        almacen_name = almacen
                        break
                products = get_products_with_sku(almacenes[almacen_name], oc.sku)
                count = 0
                for product in products:
                    # print("enviando {}".format(product['_id']))
                    send_product(product['_id'], oc.oc_id, 'CualquierDireccion', oc.price)
                    count += 1
                    if count >= oc.amount:
                        break
                oc.finished = True
                oc.save()
            else:
                try:
                    producir_10mil(oc.sku, oc.amount)
                except:
                    pass

def check_if_need_something(needs_dict): 
    for _, amount in needs_dict.items():
        if amount != 0: 
            return False
    return True

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
        # print("Conexión establecida con servidor STFP!")
        sftp.cwd('/pedidos')
        dir_structure = sftp.listdir_attr()
        for attr in dir_structure:
            # print(attr)
            with sftp.open(attr.filename) as archivo:
                file_entity = File.objects.filter(filename=attr.filename)
                must_process = False
                if not file_entity:
                    must_process = True
                tree = ET.parse(archivo)
                root = tree.getroot()
                if must_process:
                    for node in root:
                        # print(node)
                        if node.tag == 'id':
                            oc_id = node.text
                            # print(oc_id)
                            raw_response = getOc(oc_id)
                            if raw_response:
                                response = raw_response[0]
                                # print(response)
                                deadline = response["fechaEntrega"].replace("T", " ").replace("Z","")
                                recieve_response = receiveOc(oc_id)
                                if 'error' not in recieve_response[0].keys():
                                    print('pasando if')
                                    file_entity= File.objects.create(filename=attr.filename,
                                                            processed=True,
                                                            attended=False)
                                    new_oc = PurchaseOrder.objects.create(oc_id=response["_id"], sku=response['sku'], client=response['cliente'], provider=response['proveedor'],
                                                                    amount=response['cantidad'], price=response["precioUnitario"], channel=response['canal'], deadline=deadline, finished=False)
                                    file_entity.save()
                                    new_oc.save()
                                else:
                                    print('Error: {}'.format(recieve_response['error']))
