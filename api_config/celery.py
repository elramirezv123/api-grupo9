import os
from celery import Celery


#  https://djangopy.org/how-to/handle-asynchronous-tasks-with-celery-and-django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_config.settings')

app = Celery('api_config')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'thread-check-600-seconds': {  #name of the scheduler
        'task': 'thread-check',  # task name which we have created in tasks.py
        'schedule': 600.0,   # set the period of running
                            # set the args
    },

    'thread-check-10000-1200-seconds': {  #name of the scheduler
    'task': 'thread-check-10000',  # task name which we have created in tasks.py
    'schedule': 1200.0,   # set the period of running
                        # set the args
    },
        'watch-server-900-seconds': {  #name of the scheduler
        'task': 'watch-server',  # task name which we have created in tasks.py
        'schedule': 900.0,   # set the period of running
                            # set the args
    }
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request)) 
