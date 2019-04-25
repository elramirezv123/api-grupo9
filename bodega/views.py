from django.http import JsonResponse
from .helpers.functions import get_skus_with_stock
from .constants import almacenes

# https://www.webforefront.com/django/accessurlparamstemplates.html

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


def pedidos(request, almacenId):
    # Debe ser método PUT y UPDATE
    if request.method == 'PUT':
        pass
    elif request.method == 'DELETE':
        pass

def orders(request):
    pass

