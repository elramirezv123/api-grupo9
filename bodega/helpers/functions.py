from bodega.constants.logic_constants import almacen_stock, headers, minimum_stock, minimum_stock_10000, prom_request, DELTA, sku_products, REQUEST_FACTOR
from bodega.constants.config import almacenes, id_grupos
from bodega.models import Product, Ingredient, Request, PurchaseOrder
from bodega.helpers.bodega_functions import get_skus_with_stock, get_almacenes, get_products_with_sku, send_product
from bodega.helpers.bodega_functions import make_a_product, move_product_inter_almacen, move_product_to_another_group
from bodega.helpers.oc_functions import newOc, updateOC, getOc
from bodega.helpers.utils import toMiliseconds
import requests
import json
import os
import time
import random
import datetime
import pytz

PRODUCTS_JSON_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'productos.json'))

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


def get_request_body(request):
    body_unicode = request.body.decode('utf-8')
    return json.loads(body_unicode)


def get_inventory():
    #Con esta funcion obtengo todo el stock de todos los sku para cada almacén
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


def thread_check_10000():
    current_stocks, current_sku_stocks = get_inventory()
    print("VERIFICANDO LOS 10 mil")
    print("current stock: ", current_sku_stocks)
    minimum_stock_list = list(minimum_stock_10000.keys())  #en batches
    random.shuffle(minimum_stock_list)
    for sku in minimum_stock_list:
        try:
            print("SKU a preguntar: ", sku)
            product_current_stock = current_sku_stocks.get(sku, 0)
            print("CURRENT STOCK DE: {0} es {1}".format(sku, product_current_stock))
            if product_current_stock < int(minimum_stock_10000[sku]):        
                cantidad_faltante = int(minimum_stock_10000[sku]) - product_current_stock
                pedidos = PurchaseOrder.objects.filter(sku=int(sku), state="creada") | PurchaseOrder.objects.filter(sku=int(sku), state="aceptada")
                # si es asi, entonces voy a verificar si ha sido terminada con get oc
                cant = 0
                for ped in pedidos:
                    c = getOc(ped.oc_id)[0]
                    if(c.state.upper() != "TERMINADA"):
                        now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
                        deadline = ped.deadline.replace(tzinfo=pytz.UTC)
                        print("NOW: {0}, DEADLINE: {1}".format(now, deadline))
                        if deadline > now:
                            cant += ped.amount
                        else:
                            # YA PASO SU HORA, HAY QUE BORRARLO
                            ped.state = "vencida"
                    else:
                        ped.state = c.state
                cantidad_faltante -= cant
                print("CANTIDAD A LA ESPERA DE LLEGADA: ", cant)
                print("CANTIDAD A PEDIR: ", cantidad_faltante)
                inventories = {}
                is_ok, pending = request_sku_extern(sku, cantidad_faltante, inventories)  #inventories queda poblado
                print("LA ORDEN FUE RESPONDIDA CON: ", is_ok)
                print("QUEDA PENDIENTE: ", pending)
                if pending > 0:
                    ingredients = Ingredient.objects.filter(sku_product=int(sku))
                    check_ingre = {}  #almacena sku_ing: para cuantos batch alcanza
                    for ing in ingredients:
                        # estos ingredientes seran si o si de nivel 100, por lo que no son compuestos
                        print("VERIFICANDO INGREDIENTE {0} PARA EL PRODUCTO {1}".format(ing.sku_ingredient.sku, ing.sku_product.sku))
                        ingre_sku = ing.sku_ingredient.sku  #obtenemos el sku del ingrediente
                        stock_we_have = current_sku_stocks.get(ingre_sku, 0)
                        print("STOCK QUE TENEMOS: ", stock_we_have)
                        # volume in store almacena la cantidad de ese ingrediente por producto
                        # GUARDO PARA CUANTOS BATCH del producto ME ALCANZAN ESE INGREDIENTE
                        check_ingre[ingre_sku] = int(stock_we_have)
                    
                    # una vez chequeo todos, obtengo la maxima cantidad de bach que podre producir
                    max_cant_producible = min(check_ingre.values())     
                    print("MAXIMA CANTIDAD PRODUCIBLE: ", max_cant_producible) 
                    #TODOS PRODUCEN LOS DE NIVEL 10 MIL, ENTONCES MANDO A PRODUCIR
                    if max_cant_producible > 0:
                        make_space_in_almacen("cocina", "libre2", max_cant_producible)
                        send_to_somewhere(sku, max_cant_producible, almacenes["cocina"]) 
                        make_a_product(sku, max_cant_producible)

                    if max_cant_producible < pending:
                        for ingree in check_ingre:
                            if check_ingre[ingree] == max_cant_producible:
                                print("NOS QUEDAMOS SIN INGREDIENTE {0} PARA PRODUCIR EL PRODUCTO {1}".format(ingree,sku))
                                break
        except Exception as ex:
            print("ERROR THREAD_CHECK_10000: ", ex)



def thread_check():
    '''
    current_stocks: {'almacenId': [{sku: <cantidad>}]} (cantidad por almacen)
    current_sku_stocks: {sku: <cantidad>} (cantidad total por sku)
    '''
    current_stocks, current_sku_stocks = get_inventory()
    minimum_stock_list = list(minimum_stock.keys())  #en batches
    random.shuffle(minimum_stock_list)
    inventories = {}
    for sku in minimum_stock_list:        
            if int(sku) < 10000:
                print("SKU a preguntar: ", sku)
                product_current_stock = current_sku_stocks.get(sku, 0)
                if product_current_stock < int(minimum_stock[sku]*3):        
                    try:
                        cantidad_faltante = int(minimum_stock[sku]*3) - product_current_stock
                        pedidos = PurchaseOrder.objects.filter(sku=int(sku), state="creada") | PurchaseOrder.objects.filter(sku=int(sku), state="aceptada")
                        # si es asi, entonces voy a verificar si ha sido terminada con get oc
                        cant = 0
                        for ped in pedidos:
                            c = getOc(ped.oc_id)[0]
                            if(c.state.upper() != "TERMINADA"):
                                now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
                                deadline = ped.deadline.replace(tzinfo=pytz.UTC)
                                if deadline > now:
                                    cant += ped.amount
                                else:
                                    # YA PASO SU HORA, HAY QUE BORRARLO
                                    ped.state = "vencida"
                            else:
                                ped.state = c.state
                        cantidad_faltante -= cant
                        print("CANTIDAD A LA ESPERA DE LLEGADA: ", cant)
                        print("CANTIDAD A PEDIR: ", cantidad_faltante)
                        is_ok, pending = request_sku_extern(sku, cantidad_faltante, inventories)  #inventories queda poblado
                        print("LA ORDEN FUE RESPONDIDA CON: ", is_ok)
                        print("QUEDA PENDIENTE: ", pending)
                        if not is_ok and pending > 0:
                            # VERIFICAMOS SI TENEMOS SUS INGREDIENTES    
                            # PENDING ES LA CANTIDAD QUE NO PUDE PEDIR  
                            try:            
                                request_for_ingredient(sku, pending, current_sku_stocks, inventories)
                            except Exception as ex:
                                print("ERROR request for ingrediente: ", ex)
                    except Exception as ex:
                        pending = -2
                        print("ERROR THREAD_CHECK: ", ex)
                
       
                    

def request_for_ingredient(sku, pending, current_sku_stocks, inventories):
    # OBTENEMOS LOS INGREDIENTES E ITERAMOS SOBRE ELLOS
    # VERIFICAMOS SU STOCK PARA FABRICAR LA CANTIDAD A PEDIR
    # EL sku_product SERA DE NIVEL 1000 o 100
    ingredients = Ingredient.objects.filter(sku_product=int(sku))
    check_ingre = {}  #almacena sku_ing: para cuantos batch alcanza
    print("---------------------------Ingredientes: ", [item.sku_ingredient.sku for item in ingredients])
    if len(ingredients) > 0: # es de nivel 1000
        # Si esque necesita ingredientes, verificamos si tenemos 
        # cantidad para todos los ingredientes
        for ing in ingredients:
            # estos ingredientes seran si o si de nivel 100, por lo que no son compuestos
            ingre_sku = ing.sku_ingredient.sku  #obtenemos el sku del ingrediente
            stock_we_have = current_sku_stocks.get(ingre_sku, 0)
            # volume in store almacena la cantidad de ese ingrediente por producto
            # GUARDO PARA CUANTOS BATCH del producto ME ALCANZAN ESE INGREDIENTE
            check_ingre[ingre_sku] = int(stock_we_have / ing.volume_in_store)
        
        # una vez chequeo todos, obtengo la maxima cantidad de bach que podre producir
        max_cant_producible = min(check_ingre.values())        
        # verifico si alcanza
        # mando a  producir el minimo entre max_cant y pending
        cant_a_producir = min(pending, max_cant_producible)
        # MANDO A PRODUCIR LA cantidad_a_producir
        # UN BATCH A LA VEZ PARA NO LLENAR DESPACHO
        # ASUMO QUE DESPACHO ESTA VACIO        
        copy_new_pending = cant_a_producir #en batch
        while copy_new_pending > 0:
            make_space_in_almacen("despacho", "libre2", 120, [i.sku_ingredient.sku for i in ingredients])
            for ing in ingredients:
                ing_sku = ing.sku_ingredient.sku               
                # MOVEMOS A DESPACHO LO NECESARIO PARA UN BATCH
                send_to_somewhere(ing_sku, ing.volume_in_store, almacenes["despacho"])   
            # UNA VEZ TODOS EN DESPACHO, MANDO A PRODUCIR
            produ = Product.objects.filter(sku=int(sku))
            make_a_product(sku, produ.batch)
            copy_new_pending -= 1  
        if cant_a_producir < pending:
            new_pending = pending - max_cant_producible
            # NO ALCANZA
            for ing_sku in check_ingre:
                # ACTUALIZO
                check_ingre[ing_sku] -= max_cant_producible  #saco los ingredientes que se usaron
                # AHORA REVISO POR INGREDIENTE SI ME ALCANZA PARA EL RESTO DE LOS BATCH          
                if check_ingre[ing_sku] < new_pending:
                    # NO ME ALCANZA EL INGREDIENTE PARA PRODUCIR LO QUE NECESITO
                    # VERIFICAMOS SI YO LO PRODUZCO
                    if ing_sku in sku_products:
                        make_space_in_almacen("despacho", "libre2", check_ingre[ing_sku])
                        send_to_somewhere(ing_sku, check_ingre[ing_sku], almacenes["despacho"])
                        # SI LO PRODUZCO
                        # MANDO A PRODUCIR TOD LO QUE NECESITO YA QUE ES DE NIVEL 100
                        make_a_product(ing_sku, check_ingre[ing_sku])
                    else:
                        print("EL INGREDIENTE {0} NO ES NUESTRO".format(ing_sku))
                        # NO ES NUESTRO
                        # ENTONCES DEBEMOS PEDIR LO QUE NOS FALTA PARA COMPLETAR
                        # VERIFICAMOS SI YA LO PEDIMOS, HACIENDO LA SUMA DE LOS PEDIDOS
                        pedidos = PurchaseOrder.objects.filter(sku=int(sku), state="creada") | PurchaseOrder.objects.filter(sku=int(sku), state="aceptada")
                        # si es asi, entonces voy a verificar si ha sido terminada con get oc
                        cant = 0
                        for ped in pedidos:
                            c = getOc(ped.oc_id)
                            if(c.state.upper() != "TERMINADA"):
                                now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
                                deadline = ped.deadline.replace(tzinfo=pytz.UTC)
                                print("NOW: {0}, DEADLINE: {1}".format(now, deadline))
                                if deadline > now:
                                    cant += ped.amount
                                else:
                                    # YA PASO SU HORA, HAY QUE BORRARLO
                                    ped.state = "vencida"
                            else:
                                ped.state = c.state
                        print("PASO PEDIDOS")                        
                        cantidad_ingrediente_a_pedir = pending - cant
                        if cantidad_ingrediente_a_pedir > 0:
                            is_ok, pending = request_sku_extern(ing_sku, cantidad_ingrediente_a_pedir, inventories)
                            
                            if pending:
                                print("QUEDO PENDIENTE {0} DEL INGREDIENTE {1}".format(pending, ing_sku))
                                # SOLO QUEDA LLORAR
                                # AUNQUE QUIZAS SE PODRIA REINTENTAR EN UNOS MINUTOS MAS
                                pass
            
    else: # es de nivel 100
        # CHEQUEAMOS CUANTO NOS FALTA 
        # VEMOS SI LO PRODUCIMOS
        if sku in sku_products: 
            # ES NUESTRO
            # MANDO A PRODUCIR todo LO QUE NECESITO YA QUE ES DE NIVEL 100
            make_space_in_almacen("despacho", "libre2", pending)
            send_to_somewhere(sku, pending, almacenes["despacho"])
            make_a_product(sku, pending)
        else:
            # NO ES NUESTRO
            # ENTONCES DEBEMOS PEDIR LO QUE NOS FALTA PARA COMPLETAR
            # VERIFICAMOS SI YA LO PEDIMOS, HACIENDO LA SUMA DE LOS PEDIDOS
            pedidos = PurchaseOrder.objects.filter(sku=int(sku), state="creada") | PurchaseOrder.objects.filter(sku=int(sku), state="aceptada")
            # si es asi, entonces voy a verificar si ha sido terminada con get oc
            cant = 0
            for ped in pedidos:
                c = getOc(ped.oc_id)
                if(c.state.upper() != "TERMINADA"):
                    now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
                    deadline = ped.deadline.replace(tzinfo=pytz.UTC)
                    print("NOW: {0}, DEADLINE: {1}".format(now, deadline))
                    if deadline > now:
                        cant += ped.amount
                    else:
                        # YA PASO SU HORA, HAY QUE BORRARLO
                        ped.state = "vencida"
                else:
                    ped.state = c.state
            cantidad_ingrediente_a_pedir = pending - cant  # LO QUE AUN NO SE HA PEDIDO
            is_ok, pending2 = request_sku_extern(sku, cantidad_ingrediente_a_pedir, inventories)
            if pending2:
                # SOLO QUEDA LLORAR
                # AUNQUE QUIZAS SE PODRIA REINTENTAR EN UNOS MINUTOS MAS
                pass


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
        print("Ya tengo su inventario", inventorie)
        for product in inventorie:
            gotcha = product.get("sku", False)
            if gotcha:
                if sku == gotcha:
                    try:
                        print("gotcha {}, sku: {}".format(gotcha, sku))
                        return product["total"]
                    except:
                        return False
            else:
                return False
    else:
        try:
            response = requests.get("http://tuerca{}.ing.puc.cl/inventories".format(group_number))
            response = json.loads(response.text)
            print(response)
            inventories[group_number] = response
            print("Sku que estoy preguntando: ", sku)
            #print("Response1:", response, type(response))
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


def send_oc(group_number, product, quantity):
    new_order = newOc(id_grupos['9'], id_grupos[group_number], product.sku, product.production_time, quantity, product.price, "b2b")
    print("Pude hacer nueva orden: ", new_order)
    deadline = new_order["fechaEntrega"].replace("T", " ").replace("Z","")
    new = PurchaseOrder.objects.create(oc_id=new_order["_id"], sku=product.sku, client=id_grupos["9"], provider=id_grupos[group_number],
                            amount=quantity, price=new_order["precioUnitario"], channel="b2b", deadline=deadline)
    new.save()
    """
    pone una orden de quantity productos sku al grupo group_number
    """
    headers["group"] = "9"
    body = {
            "sku": str(product.sku),
            "cantidad": quantity,
            "almacenId": almacenes["recepcion"],
            "oc": new_order["_id"]
            }
    response = requests.post("http://tuerca{}.ing.puc.cl/orders".format(group_number),
                            headers=headers, json=body)
    print("Termino el response")
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
    if choice % 2 == 0:
        productors.reverse()
    print("productores: ", productors)
    for group in productors:
        print("Preguntando a grupo", group)
        if group != "9":
            available = get_sku_stock_extern(group, sku, inventories)
            print("available: ", available)
            if available:
                to_order = int(min(pending, available))
                print("EL GRUPO {0} TIENE {1} DE {2} y NECESITAMOS {3}. PEDIREMOS {4}".format(group, available, sku, pending, to_order))
                response = send_oc(group, product, to_order)
                try:
                    print("Response.text:", response.text)
                    response = json.loads(response.text)
                    #print("Response2:", response)
                    if response["aceptado"]:
                        print("Me lo aceptaron yupi")
                        pending -= float(response["cantidad"])
                        '''
                        Se imprime que lo aceptaron sólo si no hay exception
                        '''
                        if pending <= 0:
                            return True, 0
                except Exception as err:
                    print("Este error: ", err)
                    print("RESPONSE CON ERROR: ", response)
                    continue
    return False, pending


def validate_post_body(body):
    valid_keys = ['almacenId', 'sku', 'cantidad', 'oc']
    return set(body.keys()) == set(valid_keys)

def is_our_product(sku):
    return int(sku) in sku_products

def get_inventories(view=False):
    stock, _ = get_inventory()
    if not view:
        return [{"sku": sku, "total": cantidad, "nombre": Product.objects.get(sku=sku).name} for sku,cantidad in _.items()]
    else:
        return [{"sku": sku, "total": int(cantidad*0.5), "nombre": Product.objects.get(sku=sku).name} for sku,cantidad in _.items()]



def move_products(products, almacenId):
    # Recorre la lista de productos que se le entrega y lo mueve entre almacenes (solo de nosotros)
    producto_movidos = []
    for product in products:
        producto_movidos.append(product)
        response = move_product_inter_almacen(product["_id"], almacenId)
        print(response)
    return producto_movidos

def send_to_somewhere(sku, cantidad, to_almacen):
    # Mueve el producto y la cantidad que se quiera hacia el almacen que se quiera (solo de nosotros)
    producto_movidos = []
    for almacen, almacenId in almacenes.items():
        print(almacen)
        if almacen != "despacho" and almacenId != to_almacen:
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
        remaining = amount_to_free
    else:
        remaining = available_space_to_free
    
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



def send_order_another_group(order_id):
    #esta funcion mueve el producto a despacho
    # para luego enviar ese producto al grupo que lo pidio
    order_entity = PurchaseOrder.objects.filter(oc_id=int(order_id))
    order_entity = order_entity.get()
    sku = order_entity.sku
    amount = order_entity.amount
    # movemos a despacho
    '''
    Chequear si es que podemos moverlo
    para no completar a medias una orden
    '''
    make_space_in_almacen('despacho', 'libre2', int(amount))
    productos_movidos = send_to_somewhere(sku, int(amount), almacenes["despacho"])
    # enviamos luego al grupo externo
    for product in productos_movidos:
        move_product_to_another_group(product["_id"], order_entity.client, order_entity.ocId, order_entity.price)
    # si se envio todo entonces despacho todo entonces seteamos dispatched
    updateOC(order_entity.idOc, "terminada")