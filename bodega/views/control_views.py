from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django import template
from bodega.helpers.functions import get_almacenes, get_inventory, make_a_product, make_space_in_almacen, send_to_somewhere
from bodega.models import Product, Ingredient
from bodega.constants.config import prod, almacenes
from django.shortcuts import redirect
from django import forms

class PedidosForm(forms.Form):
    sku = forms.CharField(required=True)
    cantidad = forms.CharField(required=True)


def almacenes_info(request):
    response = get_almacenes()
    for almacen in response:
        id = almacen.get("_id")
        almacen["id"] = id
    context = {'almacenes': response, 'prod': prod}
    return render(request, 'almacen.html', context)

def inventory_info(request):
    form = PedidosForm()
    current_stocks, current_sku_stocks = get_inventory()
    context = {'current_stocks': current_stocks, "current_sku_stocks": current_sku_stocks, 'form': form, 'prod': prod}
    return render(request, 'inventory.html', context)


def pedir(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PedidosForm(request.POST)
        if form.is_valid():
            sku = form.cleaned_data['sku']
            cantidad = form.cleaned_data['cantidad']
            response = make_a_product(int(sku), cantidad)
            print(response)
            return HttpResponseRedirect('inventario')

def preparar(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PedidosForm(request.POST)
        if form.is_valid():
            sku = form.cleaned_data['sku']
            ingredientes = Ingredient.objects.filter(sku_product=int(sku))
            cantidad = int(form.cleaned_data['cantidad'])
            make_space_in_almacen("pulmon", "despacho", 177)
            for ingredient in ingredientes:
                send_to_somewhere(ingredient.sku_ingredient.sku, ingredient.volume_in_store*cantidad, almacenes["despacho"])
            response = make_a_product(int(sku), cantidad)
            print(response)
            return HttpResponseRedirect('inventario')
            

# Leave the rest of the views (detail, results, vote) unchanged