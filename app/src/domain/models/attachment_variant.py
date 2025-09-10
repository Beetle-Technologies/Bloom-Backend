from typing import ClassVar

from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from src.core.database.mixins import GUIDMixin
from src.core.types import GUID


class AttachmentVariant(GUIDMixin, table=True):
    """
    Represents a variant (like a thumbnail or resized version) of an attachment blob.

    Attributes:
        id (GUID): The unique identifier for the variant.
        blob_id (GUID): The ID of the blob this variant is based on.
        variation_digest (str): A digest that uniquely identifies the variation parameters.
    """

    __table_args__ = (UniqueConstraint("blob_id", "variation_digest", name="uq_attachment_variants_blob_variation"),)

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "blob_id",
        "variation_digest",
    ]

    blob_id: GUID = Field(foreign_key="attachment_blobs.id", nullable=False)
    variation_digest: str = Field(max_length=255, nullable=False)
