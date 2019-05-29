from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .helpers.functions import thread_check, thread_check_10000, create_base_products, get_base_products
from .helpers.handling_orders import watch_server, check_not_finished

@shared_task(name='thread_check')
def wrapper(*args, **kwargs):
    thread_check()

@shared_task(name='thread_check_10000')
def wrapper2(*args, **kwargs):
    thread_check_10000()

@shared_task(name='watch_server')
def wrapper3(*args, **kwargs):
    watch_server()

@shared_task(name='check_not_finished')
def wrapper4(*args, **kwargs):
    check_not_finished()

@shared_task(name='base_products')
def wrapper5(*args, **kwargs):
    create_base_products()

@shared_task(name='get_base_products')
def wrapper6(*args, **kwargs):
    get_base_products()