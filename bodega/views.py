from django.http import JsonResponse
from .helpers.functions import get_skus_with_stock, get_stock_sku, validate_post_body, sku_exists, thread_check
from .constants import almacenes, sku_products
from .models import Request
from .models import Product
import json
from django.views.decorators.csrf import csrf_exempt
from .helpers.functions import get_request_body, get_inventary
from datetime import datetime
from datetime import timedelta

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
        for product in Product.objects.filter(sku__in=sku_products):
            response.append({ 'sku': product.sku, 'nombre': product.name, 'total': get_stock_sku(product.sku)})

    if request.method == 'DELETE':
        pass
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
        {"almacenId": "asdasd", "sku": "012301", "cantidad": "10"}
        '''
        req_body = get_request_body(request)
        req_sku = req_body['sku']
        if not sku_exists(req_sku):
            return JsonResponse({'error': 'Sku not in database'}, safe=False, status=400)
        if validate_post_body(req_body):
            request_deadline = datetime.now() + timedelta(days=10)
            request_entity = Request.objects.create(store_destination_id=req_body['almacenId'],
                                                    sku_id=req_body['sku'],
                                                    amount=req_body['cantidad'],
                                                    deadline=request_deadline)

            request_entity.save()
            request_response = {
                'id' :request_entity.id,
                'storeDestinationId' :request_entity.store_destination_id,
                'accepted' :request_entity.accepted,
                'dispatched' :request_entity.dispatched,
                'deadline' :request_entity.deadline,
            }
            return JsonResponse(request_response, safe=False, status=201)
            # check_stock(request_entity.sku_id , request_entity.amount)
        else:
            return JsonResponse({'error': 'Bad body format'}, safe=False, status=400)
    elif request.method == 'PUT':
        '''
        Espera un body de la forma:
        {"pedido_id": "1", "sku": 11, "cantidad": 0, "almacenId": "nuevo almacen", "deadline": "2019-10-29"}
        '''
        req_body = get_request_body(request)
        req_sku = req_body['sku']
        if not sku_exists(req_sku):
            return JsonResponse({'error': 'Sku not in database'}, safe=False, status=400)
        request_id = req_body['pedido_id']
        request_deadline = datetime.strptime(req_body['deadline'], '%Y-%m-%d')
        request_entity = Request.objects.filter(id=int(request_id))
        request_entity.update(store_destination_id=req_body['almacenId'],
                                                sku_id=req_body['sku'],
                                                amount=req_body['cantidad'],
                                                deadline=request_deadline)
        request_entity = request_entity.get()
        return JsonResponse({
            'id' :request_entity.id,
            'storeDestinationId' :request_entity.store_destination_id,
            'accepted' :request_entity.accepted,
            'dispatched' :request_entity.dispatched,
            'deadline' :request_entity.deadline,
        }, safe=False, status=200)
    elif request.method == 'GET':
        print(make_a_product(1010, 1))
        return JsonResponse({'data': 'hola'}, safe=False)
    return JsonResponse({'error': {'type': 'Method not implemented'}}, safe=False, status=404)
