from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .helpers.functions import testing_celery

@shared_task(name= 'testing')
def wrapper(*args, **kwargs):
    testing_celery()
