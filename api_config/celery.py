import os
from celery import Celery

#  https://djangopy.org/how-to/handle-asynchronous-tasks-with-celery-and-django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_config.settings')

app = Celery('api_config')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'thread-check': {  #name of the scheduler
        'task': 'thread-check',  # task name which we have created in tasks.py
        'schedule': 600.0,   # set the period of running
                            # set the args
    },

    'thread-check-10000': {  #name of the scheduler
        'task': 'thread-check-10000',  # task name which we have created in tasks.py
        'schedule': 1200.0,   # set the period of running
                        # set the args
    },
    'watch-server': {  #name of the scheduler
        'task': 'watch-server',  # task name which we have created in tasks.py
        'schedule': 900.0,   # set the period of running
                        # set the args
    },
    'check-not-finished': {  #name of the scheduler
        'task': 'check-not-finished',  # task name which we have created in tasks.py
        'schedule': 700.0,   # set the period of running
                            # set the args
    },
    'create-base-products': {  #name of the scheduler
        'task': 'base-products',  # task name which we have created in tasks.py
        'schedule': 1200.0,   # set the period of running
                            # set the args
    },
    'get-base-products': {  #name of the scheduler
        'task': 'get-base-products',  # task name which we have created in tasks.py
        'schedule': 1200.0,   # set the period of running
                            # set the args
    }


}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
