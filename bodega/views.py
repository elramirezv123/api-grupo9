from django.http import JsonResponse
from .helpers.functions import get_skus_with_stock
from .constants import almacenes

# https://www.webforefront.com/django/accessurlparamstemplates.html

'''
Estas son las vistas que representan los endpoints descritos en nuestra documentación.
'''

def inventario(request):
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


def new_pedido(request):
    # Debe ser metodo POST
    if request.method == 'POST':
        pass


def pedidos(request):
    # Debe ser método POST y UPDATE
    if request.method == 'POST':
        #hay que guardar el pedido en la base de datos
        #
        # {
        # "almacen_destino_id": "5f7g13d5vwe3g6k423422423",
        # "sku_id": 80,
        # "cantidad": 10
        # }
        #sku = request.POST.get('skuId', '')
        cantidad = request.POST.get('cantidad', '')
        #almacen_id = request.POST.get('almacenDestinoId', '')
        # respuesta = check_products(sku, cantidad)
        print(cantidad)
        # print(almacen_id)
        # print(cantidad)
        respuesta = True
        if respuesta:
            response = {
                "stock": 'true',
              
                "cantidad":cantidad,
                
            }   
        # else:
        #     #no hay suficiente stock
        #     response = {
        #         "stock": 'true',
        #         "sku":sku,
        #         "cantidad":cantidad,
        #         "almacen_id":almacen_id,
        #     }   
    elif request.method == 'DELETE':
        pass
    elif request.method == 'GET':
        #pense en obtener el status de un pedido si es que el put y el repsonse con los productos son asincronos
        #es decir, hago el pedido y se demoran un tiempo en entregar
        #con el get chequeo el status del pedido
       pass
    return JsonResponse(response, safe=False)




def check_products(sku, cantidad):
    #chequeo si hay stock del producto
    print(sku)
    if sku == '1':
        return True
    else:
        return False
