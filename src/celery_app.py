import os

from celery import Celery


CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')

celery = Celery(__name__)
celery.conf.broker_url = CELERY_BROKER_URL
celery.conf.result_backend = CELERY_BROKER_URL
celery.autodiscover_tasks(['tasks.email'])
