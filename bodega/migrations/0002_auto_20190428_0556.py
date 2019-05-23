# Generated by Django 2.2 on 2019-04-28 05:55

from django.db import migrations
from django.utils.text import slugify
import os
import json
from ..models import Product, Ingredient

JSON_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'productos.json'))

INGREDIENTS_JSON_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'ingredients.json'))


def populate_products(apps, schema_editor):
    fs = open(JSON_PATH, 'r')
    fs2 = open(INGREDIENTS_JSON_PATH, 'r')
    data = json.load(fs)
    ingredients_data = json.load(fs2)
    product_model = apps.get_model('bodega', 'Product')
    for product in data:
        product = product_model.objects.create(sku=int(product['sku']),
                                               price=int(
                                                   product['precio'][1:].replace(',', "")) if product['precio'] else 0,
                                               duration=float(
                                                   product['duracion']),
                                               batch=int(product['lote']),
                                               used_by=int(product["usado_por"]),
                                               production_time=int(product['tiempo_esperado']),
                                               productors=",".join(product["grupos_productores"]))
        product.save()
    
    for line in ingredients_data:
        product_instance = Product.objects.get(pk=int(line[0]))
        ingredient_instance = Product.objects.get(pk=int(line[2]))
        new_ingredient = Ingredient.objects.create(sku_product=product_instance,
                                                   sku_ingredient=ingredient_instance,
                                                   production_batch=int(line[6]),
                                                   volume_in_store=int(float(line[9])))
        new_ingredient.save()
                



class Migration(migrations.Migration):

    dependencies = [
        ('bodega', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_products),
    ]
