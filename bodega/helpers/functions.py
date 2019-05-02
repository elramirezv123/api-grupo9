from .utils import hashQuery
from ..constants import apiKey, almacenes, apiURL, headers, minimum_stock, prom_request, DELTA, sku_products, REQUEST_FACTOR
from ..models import Product, Ingredient
import requests
import json
import os
import time
import random

PRODUCTS_JSON_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'productos.json'))

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
    return response.json()


def get_products_with_sku(almacenId, sku):
    # Esta función permite obtener los primeros 100 productos (default) no vencidos
    # de algún almacén con algun sku.
    hash = hashQuery("GET"+almacenId+sku)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    response = requests.get(
        apiURL + "stock?almacenId={}&sku={}".format(almacenId, sku), headers=headers)
    return response.json()



def send_product(productId, oc, address, price):
    # Despacha un producto no vencido presenta en la bodega de
    # despacho a la dirección indicada.
    hash = hashQuery("DELETE"+productId+address+price+oc)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"productoId": productId, "oc": oc,
            "direccion": address, "precio": int(price)}
    response = requests.delete(apiURL + "stock", headers=headers, json=body)
    return response.json()


def move_product_inter_almacen(productId, almacenId):
    # Mueve un producto de un almacén a otro dentro de una misma bodega.
    hash = hashQuery("POST"+productId+almacenId)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"productoId": productId, "almacenId": almacenId}
    response = requests.post(apiURL + "moveStock", headers=headers, json=body)
    return response.json()


def move_product_to_another_group(productId, almacenId):
    # Mueve un producto no vencido desde un almacén de despacho de un grupo
    # a un almacén de recepcion de otro grupo.
    # En caso que almacén de recepción se encuentre lleno, los productos quedan en almacén pulmón.
    hash = hashQuery("POST"+productId+almacenId)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"productoId": productId, "almacenId": almacenId}
    response = requests.post(apiURL + "moveStockBodega",
                             headers=headers, json=body)

    return response.json()


# Funciones útiles para fábricar productos


def make_a_product(sku, quantity):
    # OJO: Este servicio será deprecado.
    # A través de este servicio se envían a fabricar productos con o sin materias primas.
    # Este servicio no requiere realizar el pago de la fabricación.
    hash = hashQuery("PUT"+str(sku)+str(quantity))
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"sku": str(sku), "cantidad": quantity}
    response = requests.put(
        apiURL + "fabrica/fabricarSinPago", headers=headers, json=body)
    return response.json()

# Funcions utiles para la recepción de productos


def set_hook(url):
    # Setea la url para el hook de recepción de productos.
    # En caso de estar seteada anteriormente, se actualiza el valor.
    hash = hashQuery("PUT"+url)
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    body = {"url": url}
    response = request.put(apiURL + "hook", headers=headers, json=body)
    return response.json()


def get_hook():
    hash = hashQuery("GET")
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    response = request.get(apiURL + "hook", headers=headers)
    return response.json()


def delete_hook(url):
    hash = hashQuery("DELETE")
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    response = request.delete(apiURL + "hook", headers=headers)
    return response.json()


def get_request_body(request):
    body_unicode = request.body.decode('utf-8')
    return json.loads(body_unicode)



def get_inventory():
    #con esta funcion obtengo todo el stock de todos los sku para cada lmacen
    '''
    current_stocks: {'almacenId': [{sku: <cantidad>}]} (cantidad por almacen)
    current_sku_stocks: {sku: <cantidad>} (cantidad total por sku)
    '''
    current_stocks = {}
    current_sku_stocks = {}
    for almacen, almacenId in almacenes.items():
        almacen_stocks = get_skus_with_stock(almacenId)
        dict_sku = {}
        for stock in almacen_stocks:
            dict_sku[stock['_id']] = stock['total']
            current_sku_stocks[stock['_id']] = stock['total'] + current_sku_stocks.get(stock["_id"], 0)
        current_stocks[almacen] = dict_sku
    return current_stocks, current_sku_stocks



# esta funcion chequea inventario constantemente y manda a fabricar si es necesario
# esta funcion es a la que hay que aplicarle celery
def thread_check():
    current_stocks, current_sku_stocks = get_inventory()
    print("current stock: ", current_sku_stocks)
    minimum_stock_list = list(minimum_stock.keys())
    random.shuffle(minimum_stock_list)
    for sku in minimum_stock_list:
        print("SKU a preguntar: ", sku)
        # Revisamos todos los minimos 
        product_current_stock = current_sku_stocks.get(sku, 0)
        if product_current_stock < minimum_stock[sku] + DELTA:
            cantidad = cantidad_a_pedir(sku)
            # Revisamos en los otros grupos si esque lo podemos pedir, si esque no
            # entonces revisar si lo podemos fabricar con lo que tenemos
            is_ok, pending = request_sku_extern(sku, cantidad) 
            if not is_ok:
                request_for_ingredient(sku, pending, current_sku_stocks)
            else:
                # Si estamos ok, entonces los enviamos a despacho y lo enviamos a fabricar
                send_to_somewhere(sku, cantidad, almacenes["despacho"])
                make_a_product(sku, cantidad)

    for prod in sku_products:
        cantidad = cantidad_a_pedir(prod)
        make_a_product(prod, cantidad)

def request_for_ingredient(sku, pending, current_sku_stocks):
    # Si esque no pudimos conseguir todo, veremos primero si esque necesita
    # ingredientes
    ingredients = Ingredient.objects.filter(sku_product=sku)
    if len(ingredients) > 0:
        # Si esque necesita ingredientes, veremos si los tenemos. Si esque si, enviamos
        # a procesar el producto, si esque no, entonces los pedimos
        for ingredient in ingredients:
            new_sku = ingredient.sku_ingredient.sku
            stock_we_have = current_sku_stocks.get(new_sku, 0)
            if stock_we_have > ingredient.volume_in_store:
                # Si esque tenemos lo suficiente, lo enviamos a despacho
                send_to_somewhere(new_sku, ingredient.volume_in_store, almacenes["despacho"])
            else:
                # Si esque no tenemos suficiente, pedimos a los otros grupos
                is_ok, pending = request_sku_extern(new_sku, ingredient.volume_in_store)
                if not is_ok:
                    request_for_ingredient(new_sku, pending, current_sku_stocks)
        
        # Enviamos a procesar el producto, ya que los ingredientes deberían estar en 
        # despacho
        make_a_product(sku, pending)
    else:
        return
    



# Fabricar diferencia mas algo
# una funciona para la cantidad puede ser un promedio de la cantidad para cada producto pedido
# entonces cada vez que me piden una cantidad, la entrego y luego pido la cantidad promedio de ese producto
# asi podriamos mantener un stock confiable que no salga mucho del rango
# y establecemos un minimo de peticion como por ejemplo 10


def get_stock_sku(sku, stock):
    # obtengo el total de stock que tengo para un solo sku en todos los alamacenes
    suma = 0
    for almacen in stock:
        try:
            suma += stock[almacen][sku]
        except KeyError:
            continue
    return suma



def cantidad_a_pedir(sku):
    # calcula el promedio, incluyendo la nueva cantidad pedida
    # devuelve la cantidad a pedir para un sku
    # hay que almacenar en alguna parte este promedio
    # la idea es que cuando LLEGUE un PEDIDO, si este se acepta, actualizar el valor de la suma para ese sku
    '''
    Falta un handling acá. Cuando prom_request está vacío se cae este método.
    promedio = prom_request[sku][0] / prom_request[sku][1]
    '''
    used_by_amount = Product.objects.get(sku=int(sku)).batch
    return used_by_amount * REQUEST_FACTOR

def actualizar_promedio(sku, cantidad_pedida):
    # actualiza el promedio de peticiones
    prom_request[sku][0] += cantidad_pedida


def validate_post_body(body):
    valid_keys = ['store_destination_id', 'sku_id', 'amount', 'group']
    return set(body.keys()) == set(valid_keys)


# Funciones útiles para trabajar con otros grupos
def get_sku_stock_extern(group_number, sku):
    """
    obtiene el inventario de group_number, y devuelve el numero si tengan en stock y False en otro caso
    """
    try:
        response = requests.get("http://tuerca{}.ing.puc.cl/inventories".format(group_number))
        response = json.loads(response.text)
        print("Sku que estoy preguntando: ", sku)
        print("Response1:", response, type(response))
        if len(response) > 0:
            for product in response:
                gotcha = product.get("sku", False)
                if gotcha:
                    if sku == gotcha:
                        print("gotcha {}, sku: {}".format(gotcha, sku))
                        return product["total"]
                else:
                    return False
    except Exception as err:
        print("otro error: ", err)
        return False


def place_order_extern(group_number, sku, quantity):
    """
    pone una orden de quantity productos sku al grupo group_number
    """
    print("ahora voy a pedir {} cantidad: {}".format(sku, quantity))
    headers["group"] = "9"
    body = {
            "sku": sku,
            "cantidad": quantity,
            "almacenId": almacenes["recepcion"]
            }
    response = requests.post("http://tuerca{}.ing.puc.cl/orders".format(group_number),
                            headers=headers, json=body)
    return response

def request_sku_extern(sku, quantity):
    """
    dado un sku y la cantidad a pedir, va a buscar entre todos los grupos que lo entregan y
    poner ordenes hasta cumplir la cantidad deseada
    retorna true si logro pedir quantity, y false si pidio menos
    """
    pending = float(quantity)
    product = Product.objects.get(pk=sku)
    productors = product.productors.split(",")
    choice = random.choice([1,2])
    print("choice: ", choice)
    if choice % 2 == 0:
        productors.reverse()
    print("productores: ", productors)
    for group in productors:
        print("Preguntando a grupo", group)
        if group != "9":
            available = get_sku_stock_extern(group, sku)
            print("available: ", available)
            if available:
                to_order = min(pending, float(available))
                response = place_order_extern(group, sku, to_order)
                try:
                    print(response)
                    response = json.loads(response.text)
                    print("Response2:", response)
                    print("Me lo aceptaron yupi")
                    pending -= float(response["cantidad"])
                    if pending <= 0:
                        return True, 0
                except Exception as err:
                    print("Este error: ", err)
                    return False, pending
    return False, pending


def validate_post_body(body):
    valid_keys = ['almacenId', 'sku', 'cantidad']
    return set(body.keys()) == set(valid_keys)

def is_our_product(sku):
    return int(sku) in sku_products

def get_inventories():
    stock, _ = get_inventory()
    return [{"sku": sku, "total": cantidad} for sku,cantidad in _.items()]

def move_products(products, almacenId):
    # Recorre la lista de productos que se le entrega y lo mueve entre almacenes (solo de nosotros)
    for product in products:
        move_product_inter_almacen(product["_id"], almacenId)

def send_to_somewhere(sku, cantidad, to_almacen):
    # Mueve el producto y la cantidad que se quiera hacia el almacen que se quiera (solo de nosotros)
    for almacen, almacenId in almacenes.items():
        if almacen != "despacho":
            products = get_products_with_sku(almacenId, sku)
            diff = len(products) - cantidad
            try:
                if diff >= 0:
                    move_products(products[:cantidad], to_almacen)
                    return True
                else:
                    move_products(products, to_almacen)
                    cantidad -= len(products)
            except:
                return False


