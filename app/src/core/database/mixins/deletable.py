from datetime import datetime

from sqlmodel import TIMESTAMP, Field


class DeletableMixin:
    """
    Mixin that adds a deleted flag to a model.

    Attributes:
        deleted_datetime (datetime | None): The datetime when the record was deleted.
    """

    deleted_datetime: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
    )
