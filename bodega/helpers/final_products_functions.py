import pysftp
import xml.etree.ElementTree as ET
import json
import requests
from collections import defaultdict
from bodega.models import File, PurchaseOrder, Ingredient, Product
from bodega.helpers.oc_functions import getOc, receiveOc
from bodega.helpers.bodega_functions import *
from bodega.constants.config import ocURL, almacenes
from .utils import hashQuery
from bodega.constants.logic_constants import *
from bodega.helpers.functions import *


######### VERSIÓN 1 
def try_to_produce_highlevel(sku, amount, sku_inventory, almacen_inventory):
    # we_need es un diccionario de la forma:
    # {<sku_ingrediente>: <cantidad_a_enviar_a_producir>} 
    needed_to_request = get_needed_dict(sku, amount, sku_inventory)
    print(needed_to_request)

    if not check_if_doesnt_have_all(needed_to_request):
        print("Tenemos de todo!")
    #     kitchen_space_needed = sum([ amount for _, amount in ing_with_amount_to_produce.items()])
    #     # Hacemos el espacio en la cocina
    #     make_space_in_almacen('cocina', "libre1", kitchen_space_needed + 5)
    #     # Movemos los ingredientes a la cocina
    #     for sku, amount in ing_with_amount_to_produce:
    #         send_to_somewhere(sku, amount, almacenes['cocina'])
    #     # Producimos!
    #     make_a_product()
    else:
        print('No tenemos de todo :(')
        # response = make_a_product(sku, total_to_make)
        for needed_sku, needed_amount in needed_to_request.items():
            produce_mid_level(needed_sku, needed_amount, sku_inventory, almacen_inventory)
        # print(response)
        
######## VERSIÓN 2
def try_to_produce_highlvl(sku, amount, sku_inventory, almacen_inventory):
    base_products_dict = sku_base_products(sku, amount)
    needed = {}
    print(sku_inventory)
    for needed_sku, needed_amount in base_products_dict.items():
        # Vemos si lo tenemos en alguna cantidad..
        have_sku = str(needed_sku) in sku_inventory.keys()
        if have_sku:
            # Vemos si no tenemos suficiente...
            if sku_inventory[str(needed_sku)] <= needed_amount:
                # Necesitamos pedir la diferencia
                needed[str(needed_sku)] = needed_amount - sku_inventory[str(needed_sku)]
        else:
            needed[str(needed_sku)] = needed_amount
    make_related_base_skus(base_products_dict)
    # needed_to_request = get_needed_dict(sku, amount, sku_inventory)
    # for needed_sku, needed_amount in needed_to_request.items():
    #     produce_mid_level(needed_sku, needed_amount, sku_inventory, almacen_inventory)

def produce_mid_level(sku, amount, sku_inventory, almacen_inventory):
    if not has_ingredients(sku):
        # Acá no deberían entrar skus base.
        return
    needed_to_request = get_needed_dict(sku, amount, sku_inventory)
    remaining = check_if_doesnt_have_all(needed_to_request)
    if remaining:
        for remaining_sku, remaining_amount in remaining.items():
            produce_mid_level(remaining_sku, remaining_amount, sku_inventory, almacen_inventory)
    else:
        print('Tenemos de todo para producir {} de el sku {}'.format(amount, sku))
        for needed_sku, needed_amount in needed_to_request.items():
            response_move = send_to_somewhere(needed_sku, needed_amount, almacenes["despacho"])
            print(response_move)
            
        # response = make_a_product(sku, amount)
        # print(response)

def get_needed_dict(sku, amount, sku_inventory):
    """
    Devuelve un diccionario con los skus y cantidades necesarios para producir el sku que recibe como parámetro
    OJO: Son los ingredientes directos, a diferencia de sku_base_products que devuelve sólo productos bases
    {<product_sku>: <cantidad_necesaria_a_producir>}
    """
    # Los ingredientes del sku
    ingredients = Ingredient.objects.filter(sku_product_id=sku)
    # Un diccionario de la forma {<sku_ingrediente>: <cantidad_necesaria>}
    ing_with_amount_to_produce = {str(ing.sku_ingredient_id): ing.volume_in_store*amount for ing in ingredients}
    # Diccionario para chequear si tenemos de todo.
    # Es de la forma {<sku_ingrediente>: <cantidad_que_falta>}
    we_need = {sku: amount for sku, amount in ing_with_amount_to_produce.items()}

    needed_skus = [ing.sku_ingredient_id for ing in ingredients]
    
    # Recorremos nuestros stock de cada sku

    for sku, stock in sku_inventory.items():

        # Si es que el sku es requerido
        if int(sku) in needed_skus:

            # Tenemos este sku en stock. Revisamos si tenemos la cantidad necesaria

            if stock >= ing_with_amount_to_produce[sku]:
                we_need[sku] = 0
            else: 
                we_need[sku] = we_need[sku] - stock
    request_dict = {}

    # Esta parte es para considerar los tamaños de los batches.

    for needed_sku, needed_amount in we_need.items():
        total_to_make = get_batch_amount_to_produce(needed_sku, needed_amount)
        request_dict[needed_sku] = total_to_make

    return request_dict


def sku_base_products(sku, amount):
    """
    Retorna un diccionario con todos los sku_base_products del sku.
    RETURNS:
    {<base_product_sku>: <cantidad_necesaria_a_producir>}
    """
    ingredients = has_ingredients(sku)
    to_return = defaultdict(lambda: 0)
    if ingredients:
        for ing_sku in ingredients:
            total_to_make = get_batch_amount_to_produce(ing_sku.sku_ingredient_id, amount)
            if has_ingredients(ing_sku.sku_ingredient_id):
                ing_dict = sku_base_products(ing_sku.sku_ingredient_id, total_to_make)
                for k, v in ing_dict.items():
                    to_return[k] += v
            else:
                to_return[ing_sku.sku_ingredient_id] += total_to_make
    return to_return


def has_ingredients(sku):
    """
    Retorna False si es que el sku no tiene ingredientes
    en otro caso, retorna los ingredientes.
    """
    ingredients = Ingredient.objects.filter(sku_product_id=int(sku))
    if len(ingredients) > 0:
        return ingredients
    return False

def check_if_doesnt_have_all(needs_dict):
    remaining = {}
    for sku, amount in needs_dict.items():
        if amount != 0: 
            remaining[str(sku)] = amount
    if len(remaining):
        return remaining
    return False

def get_batch_amount_to_produce(sku, amount):
    """
    Retorna la cantidad necesaria (basado en los batches) para producir <amount> del <sku>.
    """
    if amount > 0:
        batch = Product.objects.get(sku=int(sku)).batch
        batches_amount = int(amount/batch) + 1
        total_to_make = batches_amount * batch
        return total_to_make
    return 0

def make_related_base_skus(skus_dict):
    """
    Recibe un diccionario de productos base:
    {<sku>: <cantidad_a_producir>}
    y los manda a hacer.
    """
    for sku, amount in skus_dict.items():
        response = make_a_product(sku, amount)
        print(response)
