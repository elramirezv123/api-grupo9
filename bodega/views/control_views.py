from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django import template
from bodega.helpers.functions import get_almacenes, get_inventory, make_a_product, make_space_in_almacen, send_to_somewhere
from bodega.models import Product, Ingredient, PurchaseOrder
from bodega.constants.config import prod, almacenes
from django.shortcuts import redirect
from django import forms

class PedidosForm(forms.Form):
    sku = forms.CharField(required=True)
    cantidad = forms.CharField(required=True)


class EmptyReceptionForm(forms.Form):
    space = forms.IntegerField(required=True)
    almacen_destino = forms.CharField(required=True)

def almacenes_info(request):
    empty_form = EmptyReceptionForm()
    response = get_almacenes()
    for almacen in response:
        id = almacen.get("_id")
        almacen["id"] = id
    context = {'almacenes': response, 'prod': prod, 'form': empty_form}
    return render(request, 'almacen.html', context)

def inventory_info(request):
    form = PedidosForm()
    current_stocks, current_sku_stocks = get_inventory()
    context = {'current_stocks': current_stocks, "current_sku_stocks": current_sku_stocks, 'form': form, 'prod': prod}
    return render(request, 'inventory.html', context)

def ftp_info(request):
    ocs = PurchaseOrder.objects.filter(finished=False, channel='ftp')
    ocs_info = {}
    for oc in ocs:
        ocs_info[oc.oc_id] = {"sku": oc.sku, "client": oc.client, "provider": oc.provider, "amount": oc.amount, "deadline": oc.deadline}
    return render(request, 'ftp.html', {'ocs': ocs_info})

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
            # make_space_in_almacen("despacho", "libre2", 177, [i.sku_ingredient.sku for i in ingredientes])
            response = make_a_product(int(sku), cantidad)
            print(response)
            if not response.get("sku", False):
                print([i.sku_ingredient.sku for i in ingredientes])
                for ingredient in ingredientes:
                    if str(ingredient.sku_ingredient.sku) != "1003" and str(ingredient.sku_ingredient.sku) != "1004":
                        cantidad_pedir = int((cantidad / ingredient.production_batch) * int(ingredient.for_batch))
                        send_to_somewhere(str(ingredient.sku_ingredient.sku), cantidad_pedir, almacenes["despacho"])
                response = make_a_product(int(sku), cantidad)
                print(response)
            return HttpResponseRedirect('inventario')

def vaciar(request):
    # if this is a POST request we need to process the form data
    # create a form instance and populate it with data from the request:
    make_space_in_almacen("despacho", "libre1", 177)
    return HttpResponseRedirect('inventario')

def empty_reception(request):
    # if this is a POST request we need to process the form data
    # create a form instance and populate it with data from the request:
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = EmptyReceptionForm(request.POST)
        if form.is_valid():
            space = form.cleaned_data['space']
            destino = form.cleaned_data['almacen_destino']
            try:
                space = int(space)
                make_space_in_almacen("recepcion", destino, space)
            except:
                pass
    return HttpResponseRedirect('almacenes')

# Leave the rest of the views (detail, results, vote) unchanged
