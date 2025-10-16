from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import GUID
from src.domain.models.attachment_variant import AttachmentVariant
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas.attachment import AttachmentVariantCreate, AttachmentVariantUpdate

logger = get_logger(__name__)


class AttachmentVariantRepository(BaseRepository[AttachmentVariant, AttachmentVariantCreate, AttachmentVariantUpdate]):
    """
    Repository for managing attachment variants in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AttachmentVariant, session)

    async def find_by_blob_id(self, blob_id: GUID) -> Sequence[AttachmentVariant]:
        """Find attachment variants by blob ID."""
        try:
            query = select(AttachmentVariant).filter(col(AttachmentVariant.blob_id) == blob_id)
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.attachment_variant_repository.find_by_blob_id:: error while finding variants for blob {blob_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve attachment variants",
                detail="An error occurred while retrieving attachment variants.",
                metadata={"blob_id": str(blob_id)},
            ) from e

    async def find_by_blob_and_digest(self, blob_id: GUID, variation_digest: str) -> AttachmentVariant | None:
        """Find attachment variant by blob ID and variation digest."""
        try:
            return await self.find_one_by_and_none(blob_id=blob_id, variation_digest=variation_digest)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.attachment_variant_repository.find_by_blob_and_digest:: error while finding variant: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve attachment variant",
                detail="An error occurred while retrieving attachment variant.",
                metadata={
                    "blob_id": str(blob_id),
                    "variation_digest": variation_digest,
                },
            ) from e
