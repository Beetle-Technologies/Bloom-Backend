from typing import TYPE_CHECKING

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from src.domain.models.account_type_group import AccountTypeGroup
    from src.domain.models.account_type_info import AccountTypeInfo


class AccountType(GUIDMixin, TimestampMixin, table=True):
    """
    Represents an account type in the system.

    Attributes:\n
        id (UUID): Unique identifier for the account type.
        title (str): Human-readable title for the account type.
        key (str): Unique key for the account type (e.g., 'business', 'supplier').
        created_datetime (datetime): When the account type was created.
        updated_datetime (datetime | None): When the account type was last updated.
    """

    SELECTABLE_FIELDS = [
        "id",
        "title",
        "key",
        "created_datetime",
        "updated_datetime",
    ]

    title: str = Field(sa_column=Column(String(120), nullable=False, unique=True))
    key: str = Field(
        sa_column=Column(String(64), nullable=False, unique=True, index=True)
    )

    type_infos: list["AccountTypeInfo"] = Relationship(back_populates="account_type")
    groups: list["AccountTypeGroup"] = Relationship(back_populates="account_type")
