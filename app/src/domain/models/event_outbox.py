from datetime import datetime
from typing import Any, ClassVar, Dict

from sqlalchemy import TEXT, TIMESTAMP, Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field
from src.core.database.mixins import CreatedDateTimeMixin, GUIDMixin
from src.core.types import GUID
from src.domain.enums import EventStatus


class EventOutbox(GUIDMixin, CreatedDateTimeMixin, table=True):
    """
    Represents an outbox for event processing.

    Attributes:
        id (GUID): Unique identifier for the event.
        event_type (str): Type of the event.
        entity_type (str): Type of the entity associated with the event.
        entity_id (GUID): ID of the entity associated with the event.
        payload (Dict[str, Any]): Event payload data.
        status (EventStatus): Current status of the event.
        account_id (GUID | None): ID of the account that triggered the event.
        session_id (str | None): ID of the session associated with the event.
        attempts (int): Number of processing attempts for the event.
        created_datetime (datetime): Timestamp when the event was created.
        last_attempt_at (datetime | None): Timestamp of the last processing attempt.
        error_message (str | None): Error message from the last failed processing attempt.
    """

    __tablename__ = "events_outbox"  # type: ignore

    __table_args__ = (
        Index("idx_events_outbox_status_created", "status", "created_datetime"),
        Index("idx_events_outbox_event_type", "event_type"),
    )

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "event_type",
        "entity_type",
        "entity_id",
        "payload",
        "status",
        "account_id",
        "session_id",
        "attempts",
        "last_attempt_at",
        "error_message",
        "created_datetime",
    ]

    event_type: str = Field(max_length=255, nullable=False, index=True)
    entity_type: str = Field(max_length=100, nullable=False)
    entity_id: GUID = Field(nullable=False)
    payload: Dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False, default=dict),
        description="Event payload data",
    )
    status: EventStatus = Field(sa_column=Column(TEXT(), nullable=False, default=EventStatus.PENDING))
    account_id: GUID | None = Field(
        foreign_key="accounts.id",
        nullable=True,
        description="Account that triggered this event, if applicable",
    )
    session_id: str | None = Field(
        nullable=True,
        description="Session ID associated with this event, if applicable",
    )
    attempts: int = Field(default=0, nullable=False)
    last_attempt_at: datetime | None = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=True))
    error_message: str | None = Field(
        sa_column=Column(TEXT(), nullable=True),
        description="Error message from last failed processing attempt",
    )
