from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .helpers.functions import thread_check, thread_check_10000

@shared_task(name='thread-check')
def wrapper(*args, **kwargs):
    thread_check()

@shared_task(name='thread-check-1000')
def wrapper2(*args, **kwargs):
    thread_check_10000()
