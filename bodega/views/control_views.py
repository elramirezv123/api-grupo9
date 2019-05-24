from django.http import HttpResponse
from django.shortcuts import render
from django import template
from bodega.helpers.functions import get_almacenes, get_inventory
from bodega.models import Product, Ingredient
from bodega.constants import prod


def almacenes_info(request):
    response = get_almacenes()
    for almacen in response:
        id = almacen.get("_id")
        almacen["id"] = id
    context = {'almacenes': response, 'prod': prod}
    return render(request, 'almacen.html', context)

def inventory_info(request):
    current_stocks, current_sku_stocks = get_inventory()
    print(current_stocks)
    print(current_sku_stocks)
    context = {'current_stocks': current_stocks, "current_sku_stocks": current_sku_stocks}
    return render(request, 'inventory.html', context)

# Leave the rest of the views (detail, results, vote) unchanged