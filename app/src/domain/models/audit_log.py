from typing import ClassVar

from pydantic import JsonValue
from sqlalchemy import VARCHAR, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship
from src.core.database.mixins import CreatedDateTimeMixin, UUIDMixin
from src.core.types import GUID
from src.domain.models import Account


class AuditLog(UUIDMixin, CreatedDateTimeMixin, table=True):
    """
    Represents an audit log entry in the system.

    Attributes:
        id (UUID): Unique identifier for the audit log entry.
        created_at (datetime): Timestamp when the audit log entry was created.
        action (str): The action performed that is being logged.
        details (str): Additional details about the action.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "action",
        "resource_type",
        "resource_id",
        "details",
        "ip_address",
        "user_agent",
        "account_id",
        "created_datetime",
    ]

    action: str = Field(sa_column=Column(VARCHAR(255), nullable=False))
    resource_type: str = Field(sa_column=Column(VARCHAR(255), nullable=False))
    resource_id: str = Field(sa_column=Column(VARCHAR(255), nullable=False))
    details: JsonValue = Field(
        sa_column=Column(
            JSONB(),
            nullable=True,
            default=dict,
        )
    )
    ip_address: str = Field(sa_column=Column(VARCHAR(45), nullable=True))
    user_agent: str = Field(sa_column=Column(VARCHAR(255), nullable=True))

    # Relationships
    account_id: GUID = Field(foreign_key="accounts.id", nullable=False)
    account: Account = Relationship()
