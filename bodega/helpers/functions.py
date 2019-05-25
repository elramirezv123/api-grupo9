from .utils import hashQuery
from ..constants import apiKey, almacenes, almacen_stock, apiURL, headers, minimum_stock, prom_request, DELTA, sku_products, REQUEST_FACTOR
from ..models import Product, Ingredient, Request
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

def get_almacenes():
    hash = hashQuery("GET")
    headers["Authorization"] = 'INTEGRACION grupo9:{}'.format(hash)
    response = requests.get(apiURL + "almacenes", headers=headers)
    return response.json()


def get_almacen_info(almacenName):
    response = get_almacenes()
    for almacen in response:
        if almacen[almacenName]:
            return almacen

def check_almacen(required_sku, required_amount, almacen_name):
    skus_in_almacen = get_skus_with_stock(almacenes[almacen_name])
    for available_sku in skus_in_almacen:
        sku, total = available_sku['_id'], available_sku['total']
        if (sku == str(required_sku)):
            return total >= required_amount
    return False


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
    print(response.json())
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
# # esta funcion es a la que hay que aplicarle celery
# def thread_check():
#     current_stocks, current_sku_stocks = get_inventory()
#     print("current stock: ", current_sku_stocks)
#     minimum_stock_list = list(minimum_stock.keys())
#     random.shuffle(minimum_stock_list)
#     inventories = {}
#     for sku in minimum_stock_list:
#         print("SKU a preguntar: ", sku)
#         # Revisamos todos los minimos
#         product_current_stock = current_sku_stocks.get(sku, 0)
#         if product_current_stock < minimum_stock[sku] + DELTA:
#             cantidad = cantidad_a_pedir(sku)
#             # Revisamos en los otros grupos si esque lo podemos pedir, si esque no
#             # entonces revisar si lo podemos fabricar con lo que tenemos
#             is_ok, pending = request_sku_extern(sku, cantidad, inventories)
#             if not is_ok:
#                 request_for_ingredient(sku, pending, current_sku_stocks, inventories)
#                 # maked = request_for_ingredient(sku, pending, current_sku_stocks, inventories)
#                 '''
#                 Aquí yo intentaría hacerlo no más para esta entrega, como se puede
#                 fabricar sin materia prima.
#                 '''
#                 # make_a_product(sku, cantidad)

#     for prod in sku_products:
#         cantidad = cantidad_a_pedir(prod)
#         make_a_product(prod, cantidad)


def thread_check_2():
    current_stocks, current_sku_stocks = get_inventory()
    print("current stock: ", current_sku_stocks)
    minimum_stock_list = list(minimum_stock.keys())
    random.shuffle(minimum_stock_list)
    inventories = {}
    for sku in minimum_stock_list:
        print("SKU a preguntar: ", sku)
        # Revisamos todos los minimos
        product_current_stock = current_sku_stocks.get(sku, 0)
        if product_current_stock < minimum_stock[sku] + DELTA:
            if sku < 10000:
                cantidad = (minimum_stock[sku] + DELTA) - product_current_stock
                #-------->FALTA VER SI PEDIREMOS TODA LA CANTIDAD O POR LOTES
                is_ok, pending = request_sku_extern(sku, cantidad, inventories)
                if not is_ok:
                    # VERIFICAMOS SI TENEMOS SUS INGREDIENTES    
                    # PENDING ES LA CANTIDAD QUE NO PUDE PEDIR              
                    request_for_ingredient2(sku, pending, current_sku_stocks, inventories)
                

    for prod in sku_products:
        cantidad = cantidad_a_pedir(prod)
        make_a_product(prod, cantidad)


def request_for_ingredient2(sku, pending, current_sku_stocks, inventories):
    # OBTENEMOS LOS INGREDIENTES E ITERAMOS SOBRE ELLOS
    # VERIFICAMOS SU STOCK PARA FABRICAR LA CANTIDAD A PEDIR
    # EL sku_product SERA DE NIVEL 1000 o 100
    ingredients = Ingredient.objects.filter(sku_product=int(sku))
    check_ingre = {}  #almacena sku_ing: para cuantos batch alcanza
    print("Ingredientes: ", ingredients)
    if len(ingredients) > 0: # es de nivel 1000
        # Si esque necesita ingredientes, verificamos si tenemos 
        # cantidad para todos los ingredientes
        for ing in ingredients:
            # estos ingredientes seran si o si de nivel 100, por lo que no son compuestos
            print("VERIFICANDO INGREDIENTE: ", ing.sku_product.sku, ing.sku_ingredient.sku)
            ingre_sku = ing.sku_ingredient.sku
            stock_we_have = current_sku_stocks.get(ingre_sku, 0)
            print("STOCK QUE TENEMOS: ", stock_we_have)
            # volume in store almacena la cantidad de ese ingrediente por producto
            # GUARDO PARA CUANTOS BATCH del producto ME ALCANZAN ESE INGREDIENTE
            check_ingre[ingre_sku] = stock_we_have % ing.volume_in_store
        
        # una vez chequeo todos, obtengo la maxima cantidad de bach que podre producir
        max_cant_producible = min(check_ingre.values())        
        # verifico si alcanza
        # mando a  producir el minimo entre max_cant y pending
        cant_a_producir = min(pending, max_cant_producible)
        if cant_a_producir < pending:
            # NO ALCANZA
            # NUEVO PENDING
            new_pending = pending - max_cant_producible         
            for ing_sku in check_ingre:
                # ACTUALIZO
                check_ingre[ing_sku] -= max_cant_producible          
                if check_ingre[ing_sku] < new_pending:
                    # NO ME ALCANZA EL INGREDIENTE PARA PRODUCIR LO QUE NECESITO
                    # VERIFICAMOS SI YO LO PRODUZCO
                    if ing_sku in sku_products: 
                        # LO PRODUZCO DIRECTAMENTE YA QUE ES NIVEL 100
                        #MANDO A PRODUCIR todo LO QUE NECESITO YA QUE ES DE NIVEL 100
                        make_a_product(ing_sku, check_ingre[ing_sku])
                    else:
                        # ENTONCES DEBEMOS PEDIR LO QUE NOS FALTA PARA COMPLETAR
                        # VERIFICAMOS SI YA LO PEDIMOS, HACIENDO LA SUMA DE LOS PEDIDOS
                        pedidos = Purchase_Order.objects.filter(product_sku=int(sku),ingre_sku=int(sku))
                        cant = 0
                        for ped in pedidos:
                            if ped.deadline > datetime.datetime.now():
                                cant += ped.amount
                            else:
                                ped.delete()
                        cantidad_ingrediente_a_pedir = pending - cant
                        is_ok, pending = request_sku_extern(ing_sku, cantidad_ingrediente_a_pedir, inventories)
                        if pending:
                            # SOLO QUEDA LLORAR
                            # AUNQUE QUIZAS SE PODRIA REINTENTAR EN UNOS MINUTOS MAS
                            pass
        else:
            # SI ALCANZA, ENTONCES MANDO A DESPACHO Y LUEGO A PRODUCIR,
            # UN BATCH A LA VEZ PARA NO LLENAR DESPACHO
            # ASUMO QUE DESPACHO ESTA VACIO
            copy_new_pending = new_pending  #en batch
            while copy_new_pending > 0:
                for ing in ingredients:
                    ing_sku = ing.sku_ingredient.sku               
                    # MOVEMOS A DESPACHO LO NECESARIO PARA UN BATCH
                    send_to_somewhere(ing_sku, ing.volume_in_store, almacenes["despacho"])   
                # UNA VEZ TODOS EN DESPACHO, MANDO A PRODUCIR
                make_a_product(sku, check_ingre[ing_sku])
                copy_new_pending -= 1
    else: # es de nivel 100
        #CHEQUEAMOS CUANTO NOS FALTA 
        # VEMOS SI LO PRODUCIMOS
        if sku in sku_products: 
            # LO PRODUZCO DIRECTAMENTE YA QUE ES NIVEL 100
            #MANDO A PRODUCIR todo LO QUE NECESITO YA QUE ES DE NIVEL 100
            make_a_product(sku, pending)
        else:
            # ENTONCES DEBEMOS PEDIR LO QUE NOS FALTA PARA COMPLETAR
            # VERIFICAMOS SI YA LO PEDIMOS, HACIENDO LA SUMA DE LOS PEDIDOS
            pedidos = Purchase_Order.objects.filter(product_sku=int(sku),ingre_sku=int(sku))
            cant = 0
            for ped in pedidos:
                if ped.deadline > datetime.datetime.now():
                    cant += ped.amount
                else:
                    ped.delete()
            cantidad_ingrediente_a_pedir = pending - cant
            is_ok, pending2 = request_sku_extern(sku, cantidad_ingrediente_a_pedir, inventories)
            if pending2:
                # SOLO QUEDA LLORAR
                # AUNQUE QUIZAS SE PODRIA REINTENTAR EN UNOS MINUTOS MAS
                pass
   


# def request_for_ingredient(sku, pending, current_sku_stocks, inventories):
#     # Debería retornar si es que se pudo realizar el producto.
#     # Nos interesa saber si al hacer el request "a través de los ingredientes"
#     # logramos fabricarlos.
#     # Si esque no pudimos conseguir todo, veremos primero si esque necesita
#     # ingredientes
#     ingredients = Ingredient.objects.filter(sku_product=int(sku))
#     print("Ingredientes: ", ingredients)
#     if len(ingredients) > 0:
#         # Si esque necesita ingredientes, veremos si los tenemos. Si esque si, enviamos
#         # a procesar el producto, si esque no, entonces los pedimos
#         for ingredient in ingredients:
#             print("INGREDIENTE: ", ingredient, ingredient.sku_product.sku, ingredient.sku_ingredient.sku)
#             new_sku = ingredient.sku_ingredient.sku
#             stock_we_have = current_sku_stocks.get(new_sku, 0)
#             print("STOCK QUE TENEMOS: ", stock_we_have)
#             if stock_we_have > ingredient.volume_in_store:
#                 # Si esque tenemos lo suficiente, lo enviamos a despacho
#                 '''
#                 Podríamos chequear si es que hay en despcho antes de mover las cosas
#                 para no sobrecargar despacho (además, es más rápido) (ESTÁ READY)
#                 '''
#                 in_despacho = check_almacen(new_sku, ingredient.volume_in_store, 'despacho')
#                 if not in_despacho:
#                     # Habría que hacer espacio en despacho.
#                     send_to_somewhere(new_sku, ingredient.volume_in_store, almacenes["despacho"])
#             else:
#                 # Si esque el producto lo fabricamos nosotros, envia a fabricar 
#                 if new_sku in sku_products:
#                     return make_a_product(new_sku, ingredient.volume_in_store)
#                         # Habría que hacer espacio en despacho.
                    
#                 # Si esque no tenemos suficiente, pedimos a los otros grupos
#                 is_ok, pending = request_sku_extern(new_sku, ingredient.volume_in_store,inventories)
#                 if not is_ok:
#                     '''
#                     Faltó pedir (pending es positivo). Intentemos pedir/hacer los ingredientes.
#                     '''
#                     request_for_ingredient(new_sku, pending, current_sku_stocks, inventories)
#                 '''
#                 Se pudo pedir (no hay pending). Intentemos hacer sku de nuevo
#                 Creo que debería ir el return para terminar esta rama en la recursión.
#                 '''
#                 # request_for_ingredient(sku, pending, current_sku_stocks, inventories)
#                 return 

#         # Enviamos a procesar el producto, ya que los ingredientes deberían estar en
#         # despacho
#         # make_a_product(sku, pending)
#     else:
#         '''
#         Acá no deberíamos hacer el ingrendiente base? (el que tiene 0 ingredientes para hacerse)
#         '''  
#         print("MANDO A PRODUCIR", sku)
#         make_a_product(sku, pending)
#         return



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


# def validate_post_body(body):
#     valid_keys = ['store_destination_id', 'sku_id', 'amount', 'group']
#     return set(body.keys()) == set(valid_keys)


# Funciones útiles para trabajar con otros grupos
def get_sku_stock_extern(group_number, sku, inventories):
    """
    obtiene el inventario de group_number, y devuelve el numero si tengan en stock y False en otro caso
    """
    inventorie = inventories.get(group_number, False)
    if inventorie:
        for product in inventorie:
            gotcha = product.get("sku", False)
            if gotcha:
                if sku == gotcha:
                    print("gotcha {}, sku: {}".format(gotcha, sku))
                    return product["total"]
            else:
                return False
    else:
        try:
            response = requests.get("http://tuerca{}.ing.puc.cl/inventories".format(group_number))
            response = json.loads(response.text)
            inventories["group_number"] = response
            print("Sku que estoy preguntando: ", sku)
            print("Response1:", response, type(response))
            if len(response) > 0:
                for product in response:
                    gotcha = product.get("sku", False)
                    if gotcha:
                        if sku == gotcha:
                            print("gotcha {}, sku: {}".format(gotcha, sku))
                            return product["total"]
                return False
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

def request_sku_extern(sku, quantity, inventories):
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
            available = get_sku_stock_extern(group, sku, inventories)
            print("available: ", available)
            if available:
                to_order = int(min(pending, float(available)/2))
                print(to_order)
                response = place_order_extern(group, sku, to_order)
                try:
                    print(response)
                    response = json.loads(response.text)
                    print("Response2:", response)
                    pending -= float(response["cantidad"])
                    '''
                    Se imprime que lo aceptaron sólo si no hay exception
                    '''
                    print("Me lo aceptaron yupi")
                    if pending <= 0:
                        return True, 0
                except Exception as err:
                    print("Este error: ", err)
                    continue
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
    producto_movidos = []
    for product in products:
        print(product)
        producto_movidos.append(product)
        move_product_inter_almacen(product["_id"], almacenId)
    return producto_movidos

def send_to_somewhere(sku, cantidad, to_almacen):
    # Mueve el producto y la cantidad que se quiera hacia el almacen que se quiera (solo de nosotros)
    producto_movidos = []
    for almacen, almacenId in almacenes.items():
        if almacen != "despacho":
            products = get_products_with_sku(almacenId, sku)
            diff = len(products) - cantidad
            try:
                if diff >= 0:
                    producto_movidos += move_products(products[:cantidad], to_almacen)
                    return producto_movidos
                else:
                    producto_movidos += move_products(products, to_almacen)
                    cantidad -= len(products)
            except:
                return producto_movidos


def make_space_in_almacen(almacen_name, to_almacen_name, amount_to_free, banned_sku=[]):
    '''
    La idea es hacer un espacio de <amount> en el almacen <almacen_name>
    parameters:
        - <almacen_name> (string): Nombre del almacen (despacho, pulmon, etc)
        - <to_almacen_name> (string): Nombre del almacen de destino (despacho, pulmon, etc)
        - <amount> (int): cantidad de espacio a liberar
        - <banned_sku> (lista de ints): sku que no gustaría mover.
    El parámetro banned_sku es especialmente útil si estamos intentando fabricar un producto
    y no queremos mover el resto de ingredientes de despacho.
    returns:
        - True si es que pudo hacer el espacio
        - False si es que no pudo hacer el espacio
    '''
    if to_almacen_name == 'despacho':
        # No deberíamos usar despacho para vaciar otros almacenes.
        # Aparte así es consistente con send_to_somewhere
        return False
    almacen_id = almacenes[almacen_name]
    to_almacen_id = almacenes[to_almacen_name]
    products = get_skus_with_stock(almacen_id)
    almacen_sku_dict = { product['_id']: product['total'] for product in products }
    allowed_skus = list(filter(lambda x: x[0] not in banned_sku, almacen_sku_dict.items()))
    available_space_to_free = sum(map(lambda x: x[1],allowed_skus), 0)
    if available_space_to_free >= amount_to_free:
        # Se puede liberar el espacio que se pide
        remaining = amount_to_free
        while remaining > 0:
            # Elegimos un sku
            sku = allowed_skus.pop()
            # print('Sku selected: {}'.format(sku))
            # Movemos todo de ese sku
            amount_to_move = min(almacen_sku_dict[sku[0]], remaining)
            # print('A mover {} de sku {}'.format(amount_to_move, sku[0]))
            try:
                amount_moved = len(send_to_somewhere(sku[0], amount_to_move, to_almacen_id))
            except TypeError:
                # Si es que send_to_somewhere no retorna una lista (i.e. falló)
                return False
            remaining -= amount_moved
        return True
    return False


def send_order_another_group(request_id, stock):
    #esta funcion mueve el producto a despacho
    # para luego enviar ese producto al grupo que lo pidio
    request_entity = Request.objects.filter(id=int(request_id))
    request_entity = request_entity.get()
    if not request_entity.dispatched:
        sku = request_entity.sku_id
        amount = request_entity.amount
        # movemos a despacho
        '''
        Chequear si es que podemos moverlo
        para no completar a medias una orden
        '''
        if stock[almacenes["despacho"]] + amount <= almacen_stock["despacho"]:
            productos_movidos = send_to_somewhere(sku, int(amount), almacenes["despacho"])
            # enviamos luego al grupo externo
            for product in productos_movidos:
                move_product_to_another_group(product["_id"], request_entity.store_destination_id)
            # si se envio todo entonces despacho todo entonces seteamos dispatched
            request_entity.update(dispatched=True)

        else:
            make_space_in_almacen('despacho', 'pulmon', amount)
            # hay que ver como reintentar la orden cuando si haya espacio
