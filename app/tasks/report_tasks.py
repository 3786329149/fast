from app.tasks.celery_app import celery_app


@celery_app.task(name='report.build_dashboard')
def build_dashboard_task() -> dict:
    return {'built': True}
