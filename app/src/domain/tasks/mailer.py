import asyncio

from src.core.celery import celery_app
from src.core.config import settings
from src.libs.mailer import MailerError, MailerRequest, mailer_service


@celery_app.task(
    name="send_email_task",
    autoretry_for=(MailerError,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
    queue=settings.CELERY_DEFAULT_TASKS_QUEUE,
    pydantic=True,
)
def send_email_task(
    payload: MailerRequest,
) -> None:
    asyncio.run(mailer_service.send_email(payload))
