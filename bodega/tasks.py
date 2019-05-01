from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .helpers.functions import thread_check

@shared_task(name= 'thread-check')
def wrapper(*args, **kwargs):
    print("Estoy funcionando bien")
