from bodega.constants.logic_constants import base_minimum_stock, almacen_stock, headers, minimum_stock, prom_request, sku_products
from bodega.constants.config import almacenes, id_grupos
from bodega.models import Product, Ingredient, PurchaseOrder
from bodega.helpers.bodega_functions import get_skus_with_stock, get_almacenes, get_products_with_sku, send_product
from bodega.helpers.bodega_functions import make_a_product, move_product_inter_almacen, move_product_to_another_group
from bodega.helpers.oc_functions import newOc, updateOC, getOc
from bodega.helpers.utils import toMiliseconds, logger
import requests, json, os, time, random, datetime, pytz, math

PRODUCTS_JSON_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'productos.json'))

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


def get_stock_sku(sku, stock):
    # obtengo el total de stock que tengo para un solo sku en todos los alamacenes
    suma = 0
    for almacen in stock:
        try:
            suma += stock[almacen][sku]
        except KeyError:
            continue
    return suma

# def validate_post_body(body):
#     valid_keys = ['store_destination_id', 'sku_id', 'amount', 'group']
#     return set(body.keys()) == set(valid_keys)


# Funciones útiles para trabajar con otros grupos
def get_sku_stock_extern(group_number, sku):
    """
    obtiene el inventario de group_number, y devuelve el numero si tengan en stock y False en otro caso
    """
    try:
        response = requests.get("http://tuerca{}.ing.puc.cl/inventories".format(group_number))
        response = json.loads(response.text)
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
    new_order = newOc(id_grupos['9'], id_grupos[group_number], product.sku, 1440, quantity, product.price, "b2b")
    deadline = new_order["fechaEntrega"].replace("T", " ").replace("Z","")
    deadline = datetime.datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.UTC)
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
    return response


def is_our_product(sku):
    return int(sku) in sku_products

def get_inventories(view=False):
    stock, _ = get_inventory()
    if not view:
        return [{"sku": sku, "total": cantidad, "nombre": Product.objects.get(sku=sku).name} for sku,cantidad in _.items()]
    else:
        skus_in_cocina = [int(k) for k, v in stock['cocina'].items()]
        return [{"sku": sku, "total": min(cantidad - 50, 10), "nombre": Product.objects.get(sku=sku).name} for sku,cantidad in _.items() if cantidad >= 50 and int(sku) in sku_products and int(sku) not in skus_in_cocina]


def move_products(products, almacenId):
    # Recorre la lista de productos que se le entrega y lo mueve entre almacenes (solo de nosotros)
    producto_movidos = []
    for product in products:
        producto_movidos.append(product)
        response = move_product_inter_almacen(product["_id"], almacenId)
    return producto_movidos

def send_to_somewhere(sku, cantidad, to_almacen):
    # Mueve el producto y la cantidad que se quiera hacia el almacen que se quiera (solo de nosotros)
    producto_movidos = []
    print("cantidad que quiero mover", cantidad)
    for almacen, almacenId in almacenes.items():
        print("Estoy parado en ", almacen)
        if almacen not in ["despacho", "cocina"] and almacenId != to_almacen:
            products = get_products_with_sku(almacenId, sku)
            if len(products) > 0:
                diff = len(products) - cantidad
                try:
                    if diff >= 0:
                        print("Voy a mover", len(products[:cantidad]))
                        producto_movidos += move_products(products[:cantidad], to_almacen)
                        return producto_movidos
                    else:
                        print("No puedo mover todo, asique voy a mover ", len(products))
                        producto_movidos += move_products(products, to_almacen)
                        cantidad -= len(products)
                except Exception as err:
                    print(err)
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



def send_order_another_group(order_id, almacenId):
    # esta funcion mueve el producto a despacho
    # para luego enviar ese producto al grupo que lo pidio
    order_entity = PurchaseOrder.objects.get(oc_id=order_id)
    sku = order_entity.sku
    amount = order_entity.amount
    # movemos a despacho
    '''
    Chequear si es que podemos moverlo
    para no completar a medias una orden
    '''
    if not check_space(amount, 'despacho'):
        make_space_in_almacen('despacho', random.choice(['libre2', 'libre1']), int(amount), [sku])
    productos_movidos = send_to_somewhere(sku, int(amount), almacenes["despacho"])
    productos_despacho = get_products_with_sku(almacenes["despacho"], sku)
    for producto in productos_despacho:
        move_product_to_another_group(producto["_id"], almacenId, order_id, order_entity.price)
    updateOC(order_id, "terminada")


def create_base_products():
    logger('create_base_products', 'Llamando a función')
    _, inventario = get_inventory()
    for sku in sku_products:
        if inventario.get(str(sku), 0) <= 100:
            producto = Product.objects.get(sku=sku)
            cantidad = producto.batch
            if cantidad == 1: # Esto es para el camarón que su batch es de 1, pero dura 720 horas.
                cantidad*=2 
                # De camaron serán 6.
            response = make_a_product(sku, cantidad*3)
            time.sleep(1)


def create_middle_products(skus=[]):
    logger('create_middle_products', 'Llamando a función')
    _, inventario = get_inventory()
    if not skus:
        skus = minimum_stock
    for sku in skus:
        if inventario.get(str(sku), 0) < 30:
            ingredientes = Ingredient.objects.filter(sku_product=int(sku))
            lista_a_pedir = [True if inventario.get(str(ingre.sku_ingredient.sku), False) else False for ingre in ingredientes]
            if False not in lista_a_pedir:
                cantidad = ingredientes[0].sku_product.batch
                for ingredient in ingredientes:
                    cantidad_pedir = math.ceil(cantidad / ingredient.production_batch) * ingredient.volume_in_store
                    in_despacho = _["despacho"].get(str(ingredient.sku_ingredient.sku), 0)
                    cantidad_pedir = cantidad_pedir - in_despacho
                    if cantidad_pedir > 0:
                        send_to_somewhere(str(ingredient.sku_ingredient.sku), cantidad_pedir, almacenes["despacho"])
                response = make_a_product(int(sku), cantidad)
            else:
                print("No tengo todo para producir {}".format(sku))


def get_base_products():
    logger('get_base_products', 'Llamando a función')
    _, inventario = get_inventory()
    for sku in base_minimum_stock:
        if inventario.get(str(sku), 0) < 50:
            product = Product.objects.get(sku=sku)
            productors = product.productors.split(",")
            random.shuffle(productors)
            counter = 0
            for group in productors:
                if group != "9":
                    available = get_sku_stock_extern(group, str(sku))
                    if available:
                        batch = product.batch 
                        if batch == 1:
                            batch*=3
                        to_order = int(min(batch, available))
                        try:
                            response = send_oc(group, product, to_order)
                            response = json.loads(response.text)
                            print(response)
                            if response.get('aceptado'):
                                counter+= 1
                                print("el contador es ", counter)
                            if counter >= 3:
                                break
                        except Exception as err:
                            print(err)


def get_sku(sku, group_number):
    product = Product.objects.get(sku=sku)
    available = get_sku_stock_extern(group_number, str(sku))
    if available:
        batch = product.batch 
        if batch == 1:
            batch*=3
        to_order = int(min(batch, available))
        try:
            response = send_oc(group_number, product, to_order)
            response = json.loads(response.text)
            print(response)
        except Exception as err:
            print(err)
    time.sleep(1)

def check_space(quantity, almacenName):
    almacens = get_almacenes()
    for almacen in almacens:
        if almacen["_id"] == almacenes[almacenName]:
            if quantity > (almacen['totalSpace'] - almacen['usedSpace']):
                return False
            else:
                return True


def empty_recepcion_HTTPless():
    logger('empty_recepcion_HTTPless', 'Llamando a función')
    almacens = get_almacenes()
    libres = {}
    for almacen in almacens:
        if almacen["_id"] == almacenes['libre1']:
            libres['libre1'] = almacen
        elif almacen["_id"] == almacenes['libre2']:
            libres['libre2'] = almacen
    for almacen in almacens:
        if almacen["_id"] == almacenes['recepcion']:
            pendiente_vaciar = int(almacen['usedSpace'])
            llenos = 0
            while pendiente_vaciar > 0: 
                for nombre in libres.keys():
                    libre = libres[nombre]
                    cap_disp_destino = int(libre['totalSpace']) - int(libre['usedSpace'])
                    while cap_disp_destino > 0 and pendiente_vaciar > 0:
                        cantidad = min(pendiente_vaciar, cap_disp_destino, 200)
                        try:
                            if make_space_in_almacen('recepcion', nombre, cantidad):
                                pendiente_vaciar -= cantidad
                                cap_disp_destino -= cantidad                                
                                if pendiente_vaciar == 0:
                                    break
                                if cap_disp_destino == 0:
                                    llenos += 1
                                if llenos == 2:
                                    break
                        except:
                            print("### ERROR AL VACIAR RECEPCION, TERMINANDO")


def empty_pulmon():
    logger('empty_pulmon', 'Llamando a función')
    almacens = get_almacenes()
    libres = {}
    for almacen in almacens:
        if almacen["_id"] == almacenes['libre1']:
            libres['libre1'] = almacen
        elif almacen["_id"] == almacenes['libre2']:
            libres['libre2'] = almacen
    for almacen in almacens:
        if almacen["_id"] == almacenes['pulmon']:
            pendiente_vaciar = int(almacen['usedSpace'])
            llenos = 0
            while pendiente_vaciar > 0: 
                for nombre in libres.keys():
                    libre = libres[nombre]
                    cap_disp_destino = int(libre['totalSpace']) - int(libre['usedSpace'])
                    while cap_disp_destino > 0 and pendiente_vaciar > 0:
                        cantidad = min(pendiente_vaciar, cap_disp_destino, 200)
                        try:
                            if make_space_in_almacen('pulmon', nombre, cantidad):
                                pendiente_vaciar -= cantidad
                                cap_disp_destino -= cantidad                               
                                if pendiente_vaciar == 0:
                                    break
                                if cap_disp_destino == 0:
                                    llenos += 1
                                if llenos == 2:
                                    break
                        except:
                            print("### ERROR AL VACIAR PULMON, TERMINANDO")

                
