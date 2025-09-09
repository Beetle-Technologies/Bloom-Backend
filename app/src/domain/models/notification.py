from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from src.domain.models import Account


class Notification(GUIDMixin, TimestampMixin, table=True):
    """
    Represents a notification for an account.

    Attributes:
        title (str): The title of the notification.
        message (str): The message content of the notification.
        is_read (bool): A flag indicating whether the notification has been read.
        created_datetime (datetime): The timestamp when the notification was created.
        updated_datetime (datetime | None): The timestamp when the notification was last updated.
    """

    title: str = Field(default="")
    message: str = Field(default="")
    is_read: bool = Field(sa_column=Column(Boolean(), nullable=False, default=False))

    # Relationships
    account: "Account" = Relationship(back_populates="notifications")
