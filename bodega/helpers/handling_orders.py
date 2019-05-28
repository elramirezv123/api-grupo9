import pysftp
import xml.etree.ElementTree as ET
import json
import requests
from bodega.models import File, PurchaseOrder
from bodega.helpers.oc_functions import getOc
from bodega.constants.config import ocURL, almacenes
from .utils import hashQuery
from bodega.constants.logic_constants import *
from bodega.helpers.functions import get_inventories

def check_not_finished():
    inventories = get_inventories()

    print(inventories)

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
