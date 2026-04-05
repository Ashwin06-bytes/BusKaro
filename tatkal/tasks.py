# Using Celery for periodic tasks
from celery import shared_task
from django.core.management import call_command

@shared_task
def run_open_tatkal_windows():
    """
    Periodically checks and opens tatkal windows.
    Runs every 5 minutes as configured in celery beat.
    """
    call_command('open_tatkal_windows')
