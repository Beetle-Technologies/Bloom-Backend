from sqlmodel import Field
from src.core.database.mixins import CompositeIDMixin
from src.core.types import GUID


class AccountTypeGroup(CompositeIDMixin[tuple[GUID, GUID]], table=True):
    """
    Represents a group of accounts by account type in the system.

    Attributes:\n
        account_type_id (UUID): The unique identifier for the account type.
        account_id (UUID): The unique identifier for the account.
        assigned_by (UUID | None): The unique identifier for the user who assigned the account to the group.
    """

    SELECTABLE_FIELDS = [
        "account_type_id",
        "account_id",
        "assigned_by",
    ]

    account_type_id: GUID = Field(primary_key=True, index=True, nullable=False, foreign_key="account_type.id")
    account_id: GUID = Field(primary_key=True, index=True, nullable=False, foreign_key="accounts.id")

    assigned_by: GUID | None = Field(default=None, nullable=True)
