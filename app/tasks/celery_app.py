from celery import Celery

from app.bootstrap.logging import configure_logging
from app.config import get_config

configure_logging()
config = get_config()
celery_app = Celery('mall_enterprise', broker=config.REDIS_URL, backend=config.REDIS_URL)
celery_app.conf.task_default_queue = 'default'
celery_app.conf.worker_hijack_root_logger = False
