from .send_success_email import send_success_email #noqa
from .send_unsubscribe import send_unsubscribe, send_unsubscribe_error #noqa

from ecosante.extensions import celery
from ecosante.inscription.models import Inscription
from celery.schedules import crontab

@celery.task
def deactivate_accounts():
    Inscription.deactivate_accounts()

@celery.on_after_configure.connect
def setup_periodic_inscriptions_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='0', hour='6', day_of_week='*/1'),
        deactivate_accounts.s()
    )