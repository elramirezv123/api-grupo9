import os
from celery import Celery
from celery.schedules import crontab

#  https://djangopy.org/how-to/handle-asynchronous-tasks-with-celery-and-django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_config.settings')

app = Celery('api_config')
app.config_from_object('django.conf:settings', namespace='CELERY')

# https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#crontab-schedules

app.conf.beat_schedule = {
    'watch-server': { 
        'task': 'watch-server',  
        'schedule': crontab(minute='*/5'),   
    },
    'check-not-finished': { 
        'task': 'check-not-finished', 
        'schedule': crontab(minute='*/15'),
        'relative': True  
    },
    'check-not-initiated': {  
        'task': 'check-not-initiated',  
        'schedule': crontab(minute='*/10'),   
    },
    'create-base-products': {  
        'task': 'base-products',  
        'schedule': crontab(minute='*/20'),   
    },
    'get-base-products': {  
        'task': 'get-base-products',  
        'schedule': crontab(minute='*/20'),   
    },
    'empty-pulmon': {  
        'task': 'empty-pulmon',  
        'schedule': crontab(minute='*/20'),   
    }
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
