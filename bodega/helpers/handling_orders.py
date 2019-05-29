import pysftp
import xml.etree.ElementTree as ET
import json
import requests
from bodega.models import File, PurchaseOrder, Ingredient
from bodega.helpers.oc_functions import getOc
from bodega.helpers.bodega_functions import *
from bodega.constants.config import ocURL, almacenes
from .utils import hashQuery
from bodega.constants.logic_constants import *
from bodega.helpers.functions import *


# def try_to_produce_highlevel(sku, amount, inventories):
#     ingredients = Ingredient.objects.filter(sku_product_id=sku)
#     ing_with_amount_to_produce = {str(ing.sku_ingredient_id): ing.volume_in_store*amount for ing in ingredients}
#     needed_skus = [ing.sku_ingredient_id for ing in ingredients]
#     have_enough = True
#     for sku_info in inventories:
#         if int(sku_info['sku']) in needed_skus:
#             if int(sku_info['total']) < ing_with_amount_to_produce[sku_info['sku']]:
#                 have_enough = False
#     if have_enough:
#         kitchen_space_needed = sum([ amount for _, amount in ing_with_amount_to_produce.items()])
#         # Hacemos el espacio en la cocina
#         make_space_in_almacen('cocina', "libre1", kitchen_space_needed + 5)
#         # Movemos los ingredientes a la cocina
#         for sku, amount in ing_with_amount_to_produce:
#             send_to_somewhere(sku, amount, almacenes['cocina'])
#         # Producimos!
#         make_a_product()


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
            print(oc.sku)
            try:
                stock = int(stock[oc.sku])
            except:
                continue
            if stock >= oc.amount:
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


def watch_server():
    """
    Revisa el servidor FTP y actualiza la BD con los archivos nuevos
    no revisados, crea sus correspondientes OC como no finalizadas.
    """
    HOST_NAME = 'fierro.ing.puc.cl'
    USER_NAME = 'grupo9_dev'
    USER_PASSWORD = 'kqkgKVqbGBtkbQt'
    HOST_PORT = 22
    conn_opts = pysftp.CnOpts()
    conn_opts.hostkeys = None
    with pysftp.Connection(host=HOST_NAME, username=USER_NAME, password=USER_PASSWORD, port=HOST_PORT, cnopts=conn_opts) as sftp:
        # print("Conexión establecida con servidor STFP!")
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
                                file_entity= File.objects.create(filename=attr.filename,
                                                        processed=True,
                                                        attended=False)
                                deadline = response["fechaEntrega"].replace("T", " ").replace("Z","")
                                new_oc = PurchaseOrder.objects.create(oc_id=response["_id"], sku=response['sku'], client=response['cliente'], provider=response['proveedor'],
                                                                    amount=response['cantidad'], price=response["precioUnitario"], channel=response['canal'], deadline=deadline, finished=False)
                                file_entity.save()
                                new_oc.save()
