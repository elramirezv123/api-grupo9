from .utils import hashQuery
from ..constants import apiKey, almacenes, apiURL, headers
import requests
import json

'''
Estas son funciones útiles para hacer las llamadas a la API del profe.
'''

# Funcions útiles para bodega

def get_skus_with_stock(almacenId):
    # Esta funcion permite obtener todos los sku no vencidos de algún almacén
    hash = hashQuery("GET"+almacenId)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    response = requests.get(
        apiURL + "skusWithStock?almacenId={}".format(almacenId), headers=headers)
    return response


def get_products_with_sku(almacenId, sku):
    # Esta función permite obtener los primeros 100 productos (default) no vencidos
    # de algún almacén con algun sku.
    hash = hashQuery("GET"+almacenId+sku)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    response = requests.get(
        apiURL + "stock?almacenId={}&sku={}".format(almacenId, sku), headers=headers)
    return response


def send_product(productId, oc, address, price):
    # Despacha un producto no vencido presenta en la bodega de
    # despacho a la dirección indicada.
    hash = hashQuery("DELETE"+productId+address+price+oc)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"productoId": productId, "oc": oc,
            "direccion": address, "precio": int(price)}
    response = requests.delete(apiURL + "stock", headers=headers, data=body)
    return response


def move_product_inter_almacen(productId, almacenId):
    # Mueve un producto de un almacén a otro dentro de una misma bodega.
    hash = hashQuery("POST"+productId+almacenId)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"productoId": productId, "almacenId": almacenId}
    response = requests.post(apiURL + "moveStock", headers=headers, data=body)


def move_product_to_another_group(productId, almacenId):
    # Mueve un producto no vencido desde un almacén de despacho de un grupo
    # a un almacén de recepcion de otro grupo.
    # En caso que almacén de recepción se encuentre lleno, los productos quedan en almacén pulmón.
    hash = hashQuery("POST"+productId+almacenId)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"productoId": productId, "almacenId": almacenId}
    response = requests.post(apiURL + "moveStockBodega",
                             headers=headers, data=body)


# Funciones útiles para fábricar productos


def make_a_product(sku, quantity):
    # OJO: Este servicio será deprecado.
    # A través de este servicio se envían a fabricar productos con o sin materias primas.
    # Este servicio no requiere realizar el pago de la fabricación.
    hash = hashQuery("PUT"+sku+quantity)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"sku": str(sku), "cantidad": quantity}
    response = request.put(
        apiURL + "fabrica/fabricarSinPago", headers=headers, data=body)
    return response

# Funcions utiles para la recepción de productos


def set_hook(url):
    # Setea la url para el hook de recepción de productos.
    # En caso de estar seteada anteriormente, se actualiza el valor.
    hash = hashQuery("PUT"+url)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"url": url}
    response = request.put(apiURL + "hook", headers=headers, data=body)
    return response


def get_hook():
    hash = hashQuery("GET")
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    response = request.get(apiURL + "hook", headers=headers)
    return response


def delete_hook(url):
    hash = hashQuery("DELETE")
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    response = request.delete(apiURL + "hook", headers=headers)
    return response


def get_request_body(request):
    body_unicode = request.body.decode('utf-8')
    return json.loads(body_unicode)
