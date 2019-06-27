from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django import template
from bodega.helpers.functions import get_almacenes, get_inventory, make_a_product, make_space_in_almacen, send_to_somewhere, empty_pulmon, empty_recepcion_HTTPless, get_sku
from bodega.models import Product, Ingredient, PurchaseOrder, Log
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
    ocs = PurchaseOrder.objects.filter(channel='ftp').reverse()
    ocs_info = {}
    for oc in ocs:
        ocs_info[oc.oc_id] = {"sku": oc.sku, "client": oc.client, "state": oc.state, "provider": oc.provider, "amount": oc.amount, "deadline": oc.deadline, "created_at": oc.created_at}
    return render(request, 'ftp.html', {'ocs': ocs_info})


def show_b2b_logs(request):
    logs = Log.objects.filter(caller='b2b').order_by('created_at').reverse()
    logs_info = map(lambda x: {"id": x.id, "caller": x.caller, "date": x.created_at.strftime("%Y/%m/%d, %H:%M:%S"), "comment": x.comment}, logs)
    print(logs_info)
    return render(request, 'b2b.html', { "logs": logs_info})

def show_logs(request):
    logs = Log.objects.all().order_by('created_at').reverse()
    logs_info = map(lambda x: {"id": x.id, "caller": x.caller, "date": x.created_at.strftime("%Y/%m/%d, %H:%M:%S"), "comment": x.comment}, filter(lambda x: x.caller != 'b2b', logs))
    return render(request, 'logs.html', { "logs": logs_info})
    
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
            if not response.get("sku", False):
                for ingredient in ingredientes:
                    if True:
                        cantidad_pedir = int((cantidad / ingredient.production_batch) * int(ingredient.for_batch)+1)
                        send_to_somewhere(str(ingredient.sku_ingredient.sku), cantidad_pedir, almacenes["despacho"])
                response = make_a_product(int(sku), cantidad)
                print(response)
            return HttpResponseRedirect('inventario')

def vaciar(request):
    # if this is a POST request we need to process the form data
    # create a form instance and populate it with data from the request:
    make_space_in_almacen("despacho", "libre1", 177)
    return HttpResponseRedirect('inventario')

def empty_reception_view(request):
    # if this is a POST request we need to process the form data
    # create a form instance and populate it with data from the request:
    '''if request.method == 'POST':
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
    return HttpResponseRedirect('almacenes')'''
    empty_recepcion_HTTPless()
    return JsonResponse({'empty_reception': 'working'}, safe=False, status=200)

def empty_pulmon_view(request):
    empty_pulmon()
    return JsonResponse({'empty_pulmon': 'working'}, safe=False, status=200)

def ask_group(request, group, sku):
    group = int(group)
    sku = int(sku)
    get_sku(sku, group)
    return JsonResponse({'get_sku': 'working'}, safe=False, status=200)

# Leave the rest of the views (detail, results, vote) unchanged
