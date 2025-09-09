from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from src.core.database.mixins import GUIDMixin


class AttachmentVariant(GUIDMixin, table=True):
    """
    Represents a variant (like a thumbnail or resized version) of an attachment blob.

    Attributes:
        id (GUID): The unique identifier for the variant.
        blob_id (UUID): The ID of the blob this variant is based on.
        variation_digest (str): A digest that uniquely identifies the variation parameters.
    """

    __table_args__ = (UniqueConstraint("blob_id", "variation_digest", name="uq_attachment_variants_blob_variation"),)

    SELECTABLE_FIELDS = [
        "id",
        "blob_id",
        "variation_digest",
    ]

    blob_id: UUID = Field(foreign_key="attachment_blobs.id", nullable=False)
    variation_digest: str = Field(max_length=255, nullable=False)
