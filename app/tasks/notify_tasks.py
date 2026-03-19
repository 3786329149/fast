from app.tasks.celery_app import celery_app


@celery_app.task(name='notify.send_sms')
def send_sms_task(phone: str, template_code: str, params: dict) -> dict:
    return {'phone': phone, 'template_code': template_code, 'params': params, 'sent': True}
