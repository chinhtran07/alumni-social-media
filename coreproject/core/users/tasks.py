from celery import shared_task
from .views import send_activity_status


@shared_task
def send_activity_status_task(user_id):
    send_activity_status(user_id)
