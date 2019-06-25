import json
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bodega.constants.config import almacenes
from bodega.helpers.handling_orders import watch_server, check_not_initiated, check_not_finished
from bodega.constants.logic_constants import sku_products
from bodega.models import Product, Ingredient, File, PurchaseOrder
from bodega.helpers.functions import *
from bodega.helpers.utils import logger, validate_post_body
from bodega.helpers.bodega_functions import get_skus_with_stock
from bodega.helpers.oc_functions import getOc, declineOc, receiveOc, newOc, anular_vencidas
from bodega.helpers.final_products_functions import has_ingredients

# https://www.webforefront.com/django/accessurlparamstemplates.html

'''
Estas son las vistas que representan los endpoints descritos en nuestra documentación.
'''


@csrf_exempt
def inventories(request):
    '''
    Devuelve el array definido en la documentación:
    [
        {
            sku: <id_sku_producto>,
            nombre: <nombre_producto>,
            total: <total_stock_producto>,
        },
        {...}
        ..
    ]
    '''
    response = []
    if request.method == 'GET':
        return JsonResponse(get_inventories(True), safe=False)

    if request.method == 'DELETE':
        pass
    return JsonResponse(response, safe=False)


@csrf_exempt
def orders(request):
    # hay que guardar el pedido en la base de datos
    '''
    Request usado:
    {"almacenId": "asdasd", "sku": "012301", "cantidad": "10", "oc": ide}
    '''
    req_body = get_request_body(request)
    req_sku = req_body['sku']
    req_oc = req_body['oc']
    order = getOc(req_oc)[0]
    group_number = request.headers.get('group') if request.headers.get('group') else 'NoHeader'
    try:
        req_sku = int(req_sku)
    except:
        declineOc(req_oc, "SKU NO SE PUEDE TRANSFORMAR A ENTERO (INT)")
        return JsonResponse({'error': "SKU NO SE PUEDE TRANSFORMAR A ENTERO (INT)"}, safe=False, status=400)
    inventories = get_inventories(True)
    related_sku = list(filter(lambda x: x['sku'] == str(req_sku), inventories))
    if (related_sku): # Si tenemos de ese sku
        if ((related_sku[0]['total'] < int(req_body['cantidad'])) or has_ingredients(related_sku[0]['sku'])): # Si no tenemos en la cantidad que nos piden
            declineOc(req_oc, "We don't have stock of that sku. Sorry")
            logger('b2b', "SKU: {} CANTIDAD: {} GRUPO: {}-> RECHAZADO (Sin cantidad)".format(req_sku, req_body['cantidad'], group_number))
            return JsonResponse({'error': "We don't have stock of that sku. Sorry"}, safe=False, status=400)
    else:
        declineOc(req_oc, "We don't have stock of that sku. Sorry")
        logger('b2b', "SKU: {} GRUPO: {} -> RECHAZADO (No tenemos de ese sku.)".format(req_sku, group_number))
        return JsonResponse({'error': "We don't have that sku. Sorry"}, safe=False, status=400)

    if validate_post_body(req_body):
        new = PurchaseOrder.objects.create(oc_id=order['_id'], sku=order['sku'], client=order['cliente'], provider=order['proveedor'],
                            amount=order['cantidad'], price=order['precioUnitario'], channel=order['canal'], deadline=order['fechaEntrega'])
        new.save()
        receiveOc(req_oc)
        send_order_another_group(new.oc_id, req_body['almacenId'])
        request_response = {
            'sku': order['sku'],
            'cantidad': order['cantidad'],
            'almacenId': order['cliente'],
            'grupoProveedor': 9,
            'aceptado': True,
            'despachado': True
        }
        logger('b2b', "SKU: {} CANTIDAD: {} GRUPO: {} -> ACEPTADO".format(order['sku'], order['cantidad'], group_number))
        return JsonResponse(request_response, safe=False, status=201)
    else:
        declineOc(req_oc, 'Bad body format')
        return JsonResponse({'error': 'Bad body format'}, safe=False, status=400)

    return JsonResponse({'error': {'type': 'Method not implemented'}}, safe=False, status=501)


def test(request):
    anular_vencidas()
    return JsonResponse({'test': 'working'}, safe=False, status=200)

def watch_server_view(request):
    watch_server()
    return JsonResponse({'watch_server_view': 'working'}, safe=False, status=200)

def check_not_initiated_view(request):
    check_not_initiated()
    return JsonResponse({'check_not_initiated_view': 'working'}, safe=False, status=200)

def check_not_finished_view(request):
    check_not_finished()
    return JsonResponse({'check_not_finished_view': 'working'}, safe=False, status=200)
    # sku = "1002"
    # cantidad = 1

    # headers["group"] = "3"
    # body = {
    #         "sku": sku,
    #         "cantidad": str(cantidad),
    #         "almacenId": "5cc7b139a823b10004d8e6d9",
    #         "oc": new["_id"]
    #         }
    # response = requests.post("http://localhost:8000/orders",
    #                         headers=headers, json=body)
    # print(response.json())
    # print(type(getOc("5cee74b0bcf7bb00048df71d")))
    # c = getOc("5cee74b0bcf7bb00048df71d")
    # print(c)
    # create_base_products()
    # get_base_products()
    # response = get_skus_with_stock(almacenes["pulmon"])
    # print(response)
    # thread_check()
    # check_not_finished()
    # current_stocks, current_sku_stocks = get_inventory()
    # request_for_ingredient('1106', 10, current_sku_stocks, {})
    # stock_almacen, stock = get_inventory()
    # try_to_produce_highlvl(20004, 1, stock, stock_almacen)
    # try_to_produce_highlevel(20004, 1, stock, stock_almacen)
    # create_base_products()
    # create_middle_products()
    # vaciar_pulmon()
    # watch_server()
    # new = newOc('lalalala', id_grupos['9'],"10013", 120, 1, 1000, 'ftp')
    # print(new)
    # print("creamos la orden de compra")
    # new_oc, created = PurchaseOrder.objects.get_or_create(oc_id=new['_id'], sku=10001, 
    #                                 client="algungrupo", provider=id_grupos['9'],
    #                                 amount=1, price=1000,
    #                                 channel='ftp', deadline=(timezone.now() + timedelta(hours=1)))
    # check_not_initiated()
    # check_not_finished()
    # empty_recepcion_HTTPless()

    
