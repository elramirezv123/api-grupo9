import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bodega.constants.config import almacenes
from bodega.helpers.handling_orders import watch_server, check_not_finished, try_to_produce_highlevel, try_to_produce_highlvl
from bodega.constants.logic_constants import sku_products
from bodega.models import Product, Ingredient, Request, File, PurchaseOrder
from bodega.helpers.functions import *
from bodega.helpers.utils import logger
from bodega.helpers.bodega_functions import get_skus_with_stock
from bodega.helpers.oc_functions import getOc, declineOc, receiveOc, newOc

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
    try:
        req_sku = int(req_sku)
    except:
        declineOc(req_oc, "SKU NO SE PUEDE TRANSFORMAR A ENTERO (INT)")
        return JsonResponse({'error': "SKU NO SE PUEDE TRANSFORMAR A ENTERO (INT)"}, safe=False, status=400)
    stock, sku_stock_dict = get_inventory()
    lista = list(map(lambda x: int(x), sku_stock_dict))
    if req_sku not in lista or int(sku_stock_dict[str(req_sku)]) < int(req_body['cantidad']):
        declineOc(req_oc, "We don't have stock of that sku. Sorry")
        return JsonResponse({'error': "We don't have stock of that sku. Sorry"}, safe=False, status=400)
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

        return JsonResponse(request_response, safe=False, status=201)
    else:
        declineOc(req_oc, 'Bad body format')
        return JsonResponse({'error': 'Bad body format'}, safe=False, status=400)

    return JsonResponse({'error': {'type': 'Method not implemented'}}, safe=False, status=501)


def test(request):
    # sku = "1002"
    # cantidad = 1
    # new = newOc('5cc66e378820160004a4c3be','5cc66e378820160004a4c3c4',"1003", 120, cantidad, 10, 'b2b')
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
    # watch_server()
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
    return JsonResponse({'test': 'working'}, safe=False, status=200)
