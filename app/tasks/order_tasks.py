from app.tasks.celery_app import celery_app


@celery_app.task(name='order.auto_cancel')
def auto_cancel_order_task(order_no: str) -> dict:
    return {'order_no': order_no, 'status': 'cancelled'}
