import os
from celery import Celery
 

#  https://djangopy.org/how-to/handle-asynchronous-tasks-with-celery-and-django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_config.settings')
 
app = Celery('api_config', broker="amqp://localhost//")
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'add-every-2-seconds': {  #name of the scheduler
        'task': 'add_2_numbers',  # task name which we have created in tasks.py
        'schedule': 2.0,   # set the period of running
        'args': (16, 16)  # set the args
    },
    'print-name-every-5-seconds': {  #name of the scheduler
        'task': 'print_msg_with_name',  # task name which we have created in tasks.py
        'schedule': 5.0,  # set the period of running
         'args': ("DjangoPY", )  # set the args
    },
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))