from django.http import JsonResponse
from .helpers.functions import get_skus_with_stock, get_products_with_sku
from .constants import almacenes
from .models import Request
from .models import Product
import json
from django.views.decorators.csrf import csrf_exempt
from .helpers.functions import get_request_body

# https://www.webforefront.com/django/accessurlparamstemplates.html

'''
Estas son las vistas que representan los endpoints descritos en nuestra documentación.
'''


def inventaries(request):
    # Este es un ejemplo, aún no está listo.
    sku = request.GET.get('sku', '')
    if sku:
        pass
    else:
        pass
    response = {
        "name": "grupo9",
        "cantidad_productos": "",
        "inventario": ""
    }

    return JsonResponse(response, safe=False)


def new_order(request):
    # Debe ser metodo POST
    if request.method == 'POST':
        pass


@csrf_exempt
def orders(request):
    # Debe ser método POST y UPDATE
    if request.method == 'POST':
        # hay que guardar el pedido en la base de datos
        '''
        Request usado:
        {"store_destination_id": "asdasd", "sku_id": "012301", "amount": "10"}
        '''
        req_body = get_request_body(request)
        request_entity = Request.objects.create(store_destination_id=req_body['store_destination_id'],
                                                sku_id=req_body['sku_id'],
                                                amount=req_body['amount'])

        request_entity.save()
        response = JsonResponse({'id': request_entity.id}, safe=False)
        check_stock(request_entity.sku_id , request_entity.amount)
    elif request.method == 'DELETE':
        pass
    elif request.method == 'GET':
        # pense en obtener el status de un pedido si es que el put y el repsonse con los productos son asincronos
        # es decir, hago el pedido y se demoran un tiempo en entregar
        # con el get chequeo el status del pedido
        pass
    else:
        response = JsonResponse({'error': {'type': 'MethodError'}}, safe=False)
    return response


def check_stock(sku_id, cantidad):
    # chequeo si hay stock del producto
    #print(sku_id)
    #product = Product.objects.get(sku=sku_id)
    print(sku_id)
    response = get_products_with_sku(almacenes["despacho"], sku_id)
    try:
        print(response.content)
    except Exception as e:
        print(str(e))
    return True