from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.attachment import Attachment
from src.domain.models.attachment_blob import AttachmentBlob
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas.attachment import AttachmentBlobCreate, AttachmentBlobUpdate, AttachmentCreate, AttachmentUpdate

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class AttachmentRepository(BaseRepository[Attachment, AttachmentCreate, AttachmentUpdate]):
    """
    Repository for managing attachments in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Attachment, session)

    async def find_by_attachable(
        self, attachable_type: str, attachable_id: GUID, name: str | None = None
    ) -> Sequence[Attachment]:
        """Find attachments by attachable entity."""
        try:
            query = select(Attachment).filter(
                col(Attachment.attachable_type) == attachable_type,
                col(Attachment.attachable_id) == attachable_id,
                col(Attachment.deleted_datetime).is_(None),
            )
            if name:
                query = query.filter(col(Attachment.name) == name)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.attachment_repository.find_by_attachable:: error while finding attachments for {attachable_type}:{attachable_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve attachments",
                detail="An error occurred while retrieving attachments.",
                metadata={
                    "attachable_type": attachable_type,
                    "attachable_id": str(attachable_id),
                },
            ) from e

    async def find_by_blob_id(self, blob_id: GUID) -> Sequence[Attachment]:
        """Find attachments by blob ID."""
        try:
            query = select(Attachment).filter(
                col(Attachment.blob_id) == blob_id,
                col(Attachment.deleted_datetime).is_(None),
            )
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.attachment_repository.find_by_blob_id:: error while finding attachments for blob {blob_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve attachments",
                detail="An error occurred while retrieving attachments.",
                metadata={"blob_id": str(blob_id)},
            ) from e

    async def create_attachment(self, attachment: AttachmentCreate) -> Attachment:
        """
        Create a new attachment.

        Args:
            attachment (AttachmentCreate): The data for the new attachment.

        Returns:
            Attachment: The created attachment object.
        """
        try:
            new_attachment = Attachment(
                name=attachment.name,
                attachable_type=attachment.attachable_type,
                attachable_id=attachment.attachable_id,
                blob_id=attachment.blob_id,
            )
            new_attachment.save_friendly_fields()
            self.session.add(new_attachment)
            await self._save_changes(new_attachment)
            return new_attachment
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.attachment_repository.create_attachment:: error while creating attachment: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to create attachment",
                detail="An error occurred while creating the attachment.",
            ) from e


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
