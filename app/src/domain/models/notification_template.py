from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import TEXT, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Account


class NotificationTemplate(GUIDMixin, TimestampMixin, table=True):
    """
    Represents a notification template stored in the database.

    Attributes:
        id (GUID): The unique identifier.
        name (str): Template name (e.g., 'v1.orders.confirmation').
        tile (str): Subject line.
        body (str): Template body with placeholders (e.g., {{name}}).
        created_by_account_id (GUID | None): Who created it.
        created_datetime (datetime): When created.
        updated_datetime (datetime | None): When updated.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "name",
        "title",
        "body",
        "created_by",
        "created_datetime",
        "updated_datetime",
    ]

    name: str = Field(max_length=100, nullable=False, unique=True)
    title: str = Field(max_length=255, nullable=False)
    body: str = Field(sa_column=Column(TEXT(), nullable=False))
    created_by: GUID | None = Field(foreign_key="accounts.id", nullable=True)

    # Relationships
    created_by_account: "Account" = Relationship()
