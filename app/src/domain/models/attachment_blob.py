from decimal import Decimal

from pydantic import JsonValue
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field
from src.core.database.mixins import CreatedDateTimeMixin, DeletableMixin, FriendlyMixin, GUIDMixin


class AttachmentBlob(GUIDMixin, FriendlyMixin, CreatedDateTimeMixin, DeletableMixin, table=True):
    """
    Represents the actual binary data for an attachment.

    Attributes:
        id (GUID): The unique identifier for the blob.
        friendly_id (str): A human-readable identifier for the blob.
        key (str): A unique key to identify the blob.
        filename (str): The name of the file.
        content_type (str): The MIME type of the file (equivalent to mime_type).
        metadata (str | None): Additional metadata about the file in JSON format.
        service_name (str): The storage service used for this blob.
        byte_size (Decimal): The size of the file in bytes.
        checksum (str | None): The checksum of the file for integrity verification.
        created_datetime (datetime): When the blob was created.
        deleted_datetime (datetime | None): When the blob was deleted, if applicable.
    """

    __table_args__ = (UniqueConstraint("key", name="uq_attachment_blobs_key"),)

    SELECTABLE_FIELDS = [
        "id",
        "friendly_id",
        "key",
        "filename",
        "content_type",
        "metadata",
        "service_name",
        "byte_size",
        "checksum",
        "created_datetime",
        "deleted_datetime",
    ]

    key: str = Field(max_length=255, index=True, sa_column_kwargs={"unique": True})
    filename: str = Field(max_length=255)
    content_type: str = Field(max_length=100)
    meta_data: JsonValue = Field(
        sa_column=Column(
            JSONB(),
            nullable=True,
            default=None,
        )
    )
    service_name: str = Field(max_length=100)
    byte_size: Decimal = Field()
    checksum: str | None = Field(max_length=128, default=None)
