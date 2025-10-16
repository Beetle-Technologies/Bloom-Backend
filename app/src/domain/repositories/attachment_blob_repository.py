from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.domain.models.attachment_blob import AttachmentBlob
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas.attachment import AttachmentBlobCreate, AttachmentBlobUpdate

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class AttachmentBlobRepository(BaseRepository[AttachmentBlob, AttachmentBlobCreate, AttachmentBlobUpdate]):
    """
    Repository for managing attachment blobs in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AttachmentBlob, session)

    async def get_by_key(self, key: str) -> AttachmentBlob | None:
        """Get attachment blob by key."""
        try:
            return await self.find_one_by_or_none(key=key)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.attachment_blob_repository.get_by_key:: error while getting blob by key {key}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve attachment blob",
                detail="An error occurred while retrieving attachment blob.",
                metadata={"key": key},
            ) from e

    async def create_blob(self, blob: AttachmentBlobCreate) -> AttachmentBlob:
        """
        Create a new attachment blob.

        Args:
            blob (AttachmentBlobCreate): The data for the new blob.

        Returns:
            AttachmentBlob: The created blob object.
        """
        try:
            new_blob = AttachmentBlob(
                key=blob.key,
                filename=blob.filename,
                content_type=blob.content_type,
                meta_data=blob.meta_data,
                service_name=blob.service_name,
                byte_size=blob.byte_size,
                checksum=blob.checksum,
            )
            new_blob.save_friendly_fields()
            self.session.add(new_blob)
            await self._save_changes(new_blob)
            return new_blob
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.attachment_blob_repository.create_blob:: error while creating blob: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to create attachment blob",
                detail="An error occurred while creating the attachment blob.",
            ) from e
