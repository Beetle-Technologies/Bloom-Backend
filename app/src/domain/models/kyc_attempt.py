from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TEXT, TIMESTAMP, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Account


class KYCAttempt(GUIDMixin, TimestampMixin, table=True):
    """
    Represents KYC verification attempts for accounts.

    Attributes:
        id (GUID): Unique identifier for the KYC attempt.
        account_id (GUID): ID of the account associated with the KYC attempt.
        is_reset (bool): Indicates if the KYC attempt was reset.
        reset_datetime (datetime | None): Datetime when the KYC attempt was reset.
        reset_reason (str | None): Reason for resetting the KYC attempt.
        created_datetime (datetime): Timestamp when the KYC attempt was created.
        updated_datetime (datetime | None): Timestamp when the KYC attempt was last updated.
    """

    __tablename__ = "kyc_attempts"  # type: ignore

    SELECTABLE_FIELDS = [
        "id",
        "account_id",
        "is_reset",
        "reset_datetime",
        "reset_reason",
        "created_datetime",
        "updated_datetime",
    ]

    account_id: GUID = Field(foreign_key="accounts.id", nullable=False)
    is_reset: bool = Field(
        default=False, description="Indicates if the KYC attempt was reset"
    )
    reset_datetime: datetime | None = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
        description="Datetime when the KYC attempt was reset",
    )
    reset_reason: str | None = Field(
        sa_column=Column(TEXT(), nullable=True),
        description="Reason for resetting the KYC attempt",
    )

    # Relationships
    account: "Account" = Relationship()
