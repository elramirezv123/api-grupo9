from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .helpers.functions import create_base_products, get_base_products, create_middle_products
from .helpers.handling_orders import watch_server, check_not_finished, check_not_initiated

@shared_task(name='watch-server')
def wrapper1(*args, **kwargs):
    watch_server()

@shared_task(name='check-not-finished')
def wrapper2(*args, **kwargs):
    check_not_finished()

@shared_task(name='check-not-initiated')
def wrapper3(*args, **kwargs):
    check_not_initiated()

@shared_task(name='base-products')
def wrapper4(*args, **kwargs):
    create_base_products()

@shared_task(name='get-base-products')
def wrapper5(*args, **kwargs):
    get_base_products()

@shared_task(name='create-mid-products')
def wrapper6(*args, **kwargs):
    create_middle_products()

# @shared_task(name='empty-pulmon')
# def wrapper5(*args, **kwargs):
#     get_base_products()

