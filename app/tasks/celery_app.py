from celery import Celery

from app.bootstrap.logging import configure_logging
from app.core.config import get_settings

configure_logging()
settings = get_settings()
celery_app = Celery('mall_enterprise', broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_default_queue = 'default'
celery_app.conf.worker_hijack_root_logger = False
