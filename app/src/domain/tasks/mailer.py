import asyncio
from typing import Any

from src.core.celery import celery_app
from src.core.config import settings
from src.libs.mailer import MailerError, MailerRequest, mailer_service


@celery_app.task(
    name="send_email_task",
    autoretry_for=(MailerError,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
    queue=settings.CELERY_DEFAULT_TASKS_QUEUE,
)
def send_email_task(
    payload: dict[str, Any],
) -> None:
    asyncio.run(mailer_service.send_email(MailerRequest.model_validate(payload)))
