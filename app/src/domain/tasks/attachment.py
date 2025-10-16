import asyncio

from src.core.celery import celery_app
from src.core.config import settings
from src.core.database.session import db_context_manager
from src.core.exceptions.errors import ServiceError
from src.libs.storage import StorageError, storage_service


@celery_app.task(
    name="delete_marked_attachments_task",
    autoretry_for=(
        ServiceError,
        StorageError,
    ),
    retry_kwargs={"max_retries": 3, "countdown": 5},
    queue=settings.CELERY_RECURRING_TASKS_QUEUE,
)
def delete_marked_attachments_task() -> None:

    async def _task() -> None:
        async with db_context_manager() as session:
            from src.domain.services.attachment_service import AttachmentService

            service = AttachmentService(session)
            await service.delete_marked_attachments(storage_service)

    asyncio.run(_task())
