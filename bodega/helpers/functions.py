from .utils import hashQuery
from ..constants import apiKey, almacenes, apiURL, headers
import requests


def get_skus_with_stock(almacenId):
    # Esta funcion permite obtener todos los sku no vencidos de algún almacén
    hash = hashQuery("GET"+almacenId)
    headers["Authorization"]='INTEGRACION grupo9:{}'.format(hash)
    response = requests.get(apiURL + "skusWithStock?almacenId={}".format(almacenId), headers=headers)
    return response
    

def get_products_with_sku(almacenId, sku):
    # Esta función permite obtener los primeros 100 productos (default) no vencidos
    # de algún almacén con algun sku.
    hash = hashQuery("GET"+almacenId+sku)
    headers["Authorization"]='INTEGRACION grupo9:{}'.format(hash)
    response = requests.get(apiURL + "skusWithStock?almacenId={}&sku={}".format(almacenId, sku), headers=headers)
    return response
