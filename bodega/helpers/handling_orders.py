from .utils import hashQuery
from bodega.constants.logic_constants import almacen_stock, minimum_stock, prom_request, DELTA, sku_products, REQUEST_FACTOR
from bodega.constants.config import ocURL, headers, almacenes
import requests
import json
import xml.etree.ElementTree as ET
import pysftp


def watch_server():
    HOST_NAME = 'fierro.ing.puc.cl'
    USER_NAME = 'grupo9_dev'
    USER_PASSWORD = 'kqkgKVqbGBtkbQt'
    HOST_PORT = 22
    conn_opts = pysftp.CnOpts()
    conn_opts.hostkeys = None
    with pysftp.Connection(host=HOST_NAME, username=USER_NAME, password=USER_PASSWORD, port=HOST_PORT, cnopts=conn_opts) as sftp:
        print("Conexión establecida con servidor STFP!")
        sftp.cwd('/pedidos')
        dir_structure = sftp.listdir_attr()
        cont = 0
        for attr in dir_structure:
            cont += 1
            with sftp.open(attr.filename) as archivo:
                tree = ET.parse(archivo)
                root = tree.getroot()
                for node in root:
                    print(node)
                    if node.tag == 'id':
                        oc_id = node.text
                        print('ID de OC: {}'.format(oc_id))
                        response = getOc(oc_id)
                        print(response)
                        fecha_entrega = response[0]['fechaEntrega']
                        print(fecha_entrega)
                        """
                        Acá debería ir el manejo del archivo, en este punto
                        tenemos el response sobre lo que involucra la orden de compra
                        """
                    else:
                        print("{}: {}".format(node.tag, node.text))
            print(attr.filename, type(attr.filename))