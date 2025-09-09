from celery import Celery
from src.core.config import settings

celery_app = Celery(
    __name__,
    include=[
        "src.domain.tasks",
    ],
)
celery_app.conf.broker_url = str(settings.REDIS_URL)  # type: ignore[arg-type]
celery_app.conf.result_expires = 4 * 60 * 60  # 4 hours
celery_app.conf.task_acks_late = True
celery_app.conf.result_backend = str(settings.REDIS_URL)  # type: ignore[arg-type]
celery_app.conf.task_default_queue = settings.CELERY_DEFAULT_TASKS_QUEUE
celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.timezone = "UTC"  # type: ignore[assignment]
