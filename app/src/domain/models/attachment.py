from uuid import UUID

from sqlalchemy import Column, String, UniqueConstraint
from sqlmodel import Field
from src.core.database.mixins import CreatedDateTimeMixin, DeletableMixin, FriendlyMixin, GUIDMixin
from src.core.types import GUID


class Attachment(GUIDMixin, FriendlyMixin, CreatedDateTimeMixin, DeletableMixin, table=True):
    """
    Represents a file attachment in the system

    This model links a record (any entity in the system) to a blob (the actual file data).

    Attributes:\n
        id (GUID): The unique identifier for the attachment.
        friendly_id (str): A human-readable identifier for the attachment.
        name (str): The name identifier for the attachment (e.g., "avatar", "document").
        record_type (str): The type of entity this attachment is associated with (e.g., account, product, etc.).
        record_id (UUID): The ID of the entity this attachment is associated with.
        blob_id (UUID): The ID of the blob containing the actual file data.
        created_datetime (datetime): When the attachment was created.
        deleted_datetime (datetime | None): The date and time when the attachment was deleted, if applicable.
    """

    __table_args__ = (
        UniqueConstraint(
            "attachable_type",
            "attachable_id",
            "name",
            "blob_id",
            name="uq_attachments_attachable_name_blob",
        ),
    )

    SELECTABLE_FIELDS = [
        "id",
        "friendly_id",
        "name",
        "attachable_type",
        "attachable_id",
        "blob_id",
        "created_datetime",
        "deleted_datetime",
    ]

    name: str = Field(max_length=255, nullable=False)
    attachable_type: str = Field(
        sa_column=Column(
            String(120),
            nullable=False,
            index=True,
        ),
    )
    attachable_id: GUID = Field(nullable=False)
    blob_id: UUID = Field(foreign_key="attachment_blobs.id", nullable=False, index=True)
