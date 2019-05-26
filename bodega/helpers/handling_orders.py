import pysftp
import xml.etree.ElementTree as ET
import json
import requests
from bodega.models import File
from bodega.helpers.oc_functions import getOc
from bodega.constants.config import ocURL, almacenes
from .utils import hashQuery
from bodega.constants.logic_constants import *


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
            with sftp.open(attr.filename) as archivo:
                file_entity = File.objects.filter(filename=attr.filename)
                must_process = False
                if not file_entity:
                    cont += 1
                    must_process = True
                else:
                    print("Ya existía: {}".format(attr.filename))
                tree = ET.parse(archivo)
                root = tree.getroot()
                if cont < 3 and must_process:
                    for node in root:
                        print(node)
                        if node.tag == 'id':
                            oc_id = node.text
                            print('ID de OC: {}'.format(oc_id))
                            response = getOc(oc_id)
                            print(response)
                            fecha_entrega = response[0]['fechaEntrega']
                            print(fecha_entrega)
                            file_entity= File.objects.create(filename=attr.filename,
                                                    processed=True,
                                                    attended=False)
                            file_entity.save()
                            """
                            Acá debería ir el manejo del archivo, en este punto
                            tenemos el response sobre lo que involucra la orden de compra
                            """
                        else:
                            print("{}: {}".format(node.tag, node.text))
            print(attr.filename, type(attr.filename))
            if cont > 3:
                break
