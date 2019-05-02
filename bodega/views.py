from django.http import JsonResponse
from .helpers.functions import get_skus_with_stock, send_order_another_group, get_stock_sku, validate_post_body, thread_check, is_our_product
from .constants import almacenes, sku_products
from .models import Request
from .models import Product, Ingredient, Request
import json
from django.views.decorators.csrf import csrf_exempt
from .helpers.functions import get_request_body, get_inventory, get_inventories, request_sku_extern, thread_check
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
        return JsonResponse(get_inventories(), safe=False)

    if request.method == 'DELETE':
        pass
    return JsonResponse(response, safe=False)


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
        try:
            req_sku = int(req_sku)
        except:
            return JsonResponse({'error': "SKU NO SE PUEDE TRANSFORMAR A ENTERO (INT)"}, safe=False, status=400)
        if not is_our_product(req_sku):
            return JsonResponse({'error': 'Sku is not produced by us'}, safe=False, status=400)
        stock, sku_stock_dict = get_inventory()
        lista = list(map(lambda x: int(x), sku_stock_dict))       
        if req_sku not in lista or int(sku_stock_dict[str(req_sku)]) < int(req_body['cantidad']):
            return JsonResponse({'error': "We don't have stock of that sku. Sorry"}, safe=False, status=400)
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
            ###
            ######  SIN PROBAR
            
            #send_order_another_group(request_entity.id)

            ####
            ######
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
        if not is_our_product(req_sku):
            return JsonResponse({'error': 'Sku is not produced by us'}, safe=False, status=400)
        _, sku_stock_dict = get_inventory()
        if req_sku not in lista or int(sku_stock_dict[str(req_sku)]) < int(req_body['cantidad']):
            return JsonResponse({'error': "We don't have stock of that sku. Sorry"}, safe=False, status=400)
            
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
        print(thread_check())
        return JsonResponse({'data': 'hola'}, safe=False)
    return JsonResponse({'error': {'type': 'Method not implemented'}}, safe=False, status=404)


def test(request):
    thread_check()