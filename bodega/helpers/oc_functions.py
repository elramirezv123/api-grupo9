from utils import hashQuery
from ..constants import almacenes, almacen_stock, minimum_stock, prom_request, DELTA, sku_products, REQUEST_FACTOR
from ..constants import ocURL, headers
import requests
import json
import xml.etree.ElementTree as ET
import pysftp


def deleteOc(ocId, reason):
    body = {"anulacion": reason}
    response = requests.delete(
        ocURL + "anular/{}".format(ocId), headers=headers, json=body)
    return response.json()


def newOc(clientId, vendorId, sku, delivery_date, quantity, unitPrice, channel, *args):
    body = {
        "cliente": clientId,
        "proveedor": vendorId,
        "sku": sku,
        "fechaEntrega": delivery_date,
        "cantidad": quantity,
        "precioUnitario": unitPrice,
        "canal": channel,
        "notas": args[0],
        "urlNotificacion": args[1]
    }
    response = requests.put(ocURL + "crear", headers=headers, json=body)
    return response.json()


def getOc(ocId):
    response = requests.get(ocURL + "obtener/{}".format(ocId), headers=headers)
    return response.json()


def receiveOc(ocId):
    body = {"_id": ocId}
    response = requests.post(
        ocURL + "recepcionar/{}".format(ocId), headers=headers)
    return response.json()

# Está repetido el nombre
# def deleteOc(ocId, reason):
#     body = {"rechazo": reason}
#     response = requests.post(ocURL + "rechazar/{}".format(ocId), headers=headers, json=body)
#     return response.json()


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


if __name__ == '__main__':
    watch_server()
