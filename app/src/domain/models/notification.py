from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import Boolean, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import AccountTypeInfo


class Notification(GUIDMixin, TimestampMixin, table=True):
    """
    Represents a notification for an account.

    Attributes:
        title (str): The title of the notification.
        message (str): The message content of the notification.
        provider (str): The provider of the notification (e.g., 'email', 'sms').
        is_read (bool): A flag indicating whether the notification has been read.
        created_datetime (datetime): The timestamp when the notification was created.
        updated_datetime (datetime | None): The timestamp when the notification was last updated.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "title",
        "message",
        "provider",
        "is_read",
        "account_type_info_id",
        "created_datetime",
        "updated_datetime",
    ]

    title: str
    message: str
    provider: str
    is_read: bool = Field(sa_column=Column(Boolean(), nullable=False, default=False))
    account_type_info_id: GUID = Field(foreign_key="account_type_infos.id", nullable=False, index=True)

    # Relationships
    account_type_info: "AccountTypeInfo" = Relationship(back_populates="notifications")
