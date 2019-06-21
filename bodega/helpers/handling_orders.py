import pysftp
import xml.etree.ElementTree as ET
import json
import requests
from collections import defaultdict
from bodega.models import File, PurchaseOrder, Ingredient, Product
from bodega.helpers.oc_functions import getOc, receiveOc
from bodega.helpers.bodega_functions import *
from bodega.constants.config import ocURL, almacenes
from .utils import hashQuery
from bodega.constants.logic_constants import *
from bodega.helpers.functions import *


######### VERSIÓN 1 
def try_to_produce_highlevel(sku, amount, sku_inventory, almacen_inventory):
    # we_need es un diccionario de la forma:
    # {<sku_ingrediente>: <cantidad_a_enviar_a_producir>} 
    needed_to_request = get_needed_dict(sku, amount, sku_inventory)
    print(needed_to_request)

    if not check_if_doesnt_have_all(needed_to_request):
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
        # response = make_a_product(sku, total_to_make)
        for needed_sku, needed_amount in needed_to_request.items():
            produce_mid_level(needed_sku, needed_amount, sku_inventory, almacen_inventory)
        # print(response)
        
######## VERSIÓN 2
def try_to_produce_highlvl(sku, amount, sku_inventory, almacen_inventory):
    base_products_dict = sku_base_products(sku, amount)
    needed = {}
    print(sku_inventory)
    for needed_sku, needed_amount in base_products_dict.items():
        # Vemos si lo tenemos en alguna cantidad..
        have_sku = str(needed_sku) in sku_inventory.keys()
        if have_sku:
            # Vemos si no tenemos suficiente...
            if sku_inventory[str(needed_sku)] <= needed_amount:
                # Necesitamos pedir la diferencia
                needed[str(needed_sku)] = needed_amount - sku_inventory[str(needed_sku)]
        else:
            needed[str(needed_sku)] = needed_amount
    needed_to_request = get_needed_dict(sku, amount, sku_inventory)
    for needed_sku, needed_amount in needed_to_request.items():
        print('Cada fvez...')
        produce_mid_level(needed_sku, needed_amount, sku_inventory, almacen_inventory)

def make_related_base_skus(skus_dict):
    for sku, amount in skus_dict.items():
        response = make_a_product(sku, amount)
        print(response)

def produce_mid_level(sku, amount, sku_inventory, almacen_inventory):
    if not has_ingredients(sku):
        # Acá no deberían entrar skus base.
        return
    needed_to_request = get_needed_dict(sku, amount, sku_inventory)
    remaining = check_if_doesnt_have_all(needed_to_request)
    if remaining:
        for remaining_sku, remaining_amount in remaining.items():
            produce_mid_level(remaining_sku, remaining_amount, sku_inventory, almacen_inventory)
    else:
        print('Tenemos de todo para producir {} de el sku {}'.format(amount, sku))
        response = make_a_product(sku, amount)
        print(response)

def get_needed_dict(sku, amount, sku_inventory):
    # Los ingredientes del sku
    ingredients = Ingredient.objects.filter(sku_product_id=sku)
    # Un diccionario de la forma {<sku_ingrediente>: <cantidad_necesaria>}
    ing_with_amount_to_produce = {str(ing.sku_ingredient_id): ing.volume_in_store*amount for ing in ingredients}
    # Diccionario para chequear si tenemos de todo.
    # Es de la forma {<sku_ingrediente>: <cantidad_que_falta>}
    we_need = {sku: amount for sku, amount in ing_with_amount_to_produce.items()}

    needed_skus = [ing.sku_ingredient_id for ing in ingredients]
    
    # Recorremos nuestros stock de cada sku

    for sku, stock in sku_inventory.items():

        # Si es que el sku es requerido
        if int(sku) in needed_skus:

            # Tenemos este sku en stock. Revisamos si tenemos la cantidad necesaria

            if stock >= ing_with_amount_to_produce[sku]:
                we_need[sku] = 0
            else: 
                we_need[sku] = we_need[sku] - stock
    request_dict = {}

    # Esta parte es para considerar los tamaños de los batches.

    for needed_sku, needed_amount in we_need.items():
        total_to_make = get_batch_amount_to_produce(needed_sku, needed_amount)
        request_dict[needed_sku] = total_to_make

    return request_dict


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


def sku_base_products(sku, amount):
    ingredients = has_ingredients(sku)
    to_return = defaultdict(lambda: 0)
    if ingredients:
        for ing_sku in ingredients:
            total_to_make = get_batch_amount_to_produce(ing_sku.sku_ingredient_id, amount)
            if has_ingredients(ing_sku.sku_ingredient_id):
                ing_dict = sku_base_products(ing_sku.sku_ingredient_id, total_to_make)
                for k, v in ing_dict.items():
                    to_return[k] += v
            else:
                to_return[ing_sku.sku_ingredient_id] += total_to_make
    return to_return


def has_ingredients(sku):
    ingredients = Ingredient.objects.filter(sku_product_id=sku)
    if len(ingredients) > 0:
        return ingredients
    return False

def check_if_doesnt_have_all(needs_dict):
    remaining = {}
    for sku, amount in needs_dict.items():
        if amount != 0: 
            remaining[str(sku)] = amount
    if len(remaining):
        return remaining
    return False

def get_batch_amount_to_produce(sku, amount):
    if amount > 0:
        batch = Product.objects.get(sku=int(sku)).batch
        batches_amount = int(amount/batch) + 1
        total_to_make = batches_amount * batch
        return total_to_make
    return 0
    