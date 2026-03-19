from app.tasks.celery_app import celery_app


@celery_app.task(name='payment.reconcile')
def reconcile_payment_task(day: str) -> dict:
    return {'day': day, 'reconciled': True}
