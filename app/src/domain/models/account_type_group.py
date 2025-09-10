from typing import TYPE_CHECKING, ClassVar

from sqlmodel import Field, Relationship
from src.core.database.mixins import CompositeIDMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models.account import Account
    from src.domain.models.account_type import AccountType


class AccountTypeGroup(CompositeIDMixin[tuple[GUID, GUID]], table=True):
    """
    Represents a group of accounts by account type in the system.

    Attributes:\n
        account_type_id (UUID): The unique identifier for the account type.
        account_id (UUID): The unique identifier for the account.
        assigned_by (UUID | None): The unique identifier for the user who assigned the account to the group.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "account_type_id",
        "account_id",
        "assigned_by",
    ]

    account_type_id: GUID = Field(primary_key=True, index=True, nullable=False, foreign_key="account_types.id")
    account_id: GUID = Field(primary_key=True, index=True, nullable=False, foreign_key="accounts.id")

    assigned_by: GUID | None = Field(default=None, nullable=True)

    # Relationships
    account_type: "AccountType" = Relationship(back_populates="groups")
    account: "Account" = Relationship()
