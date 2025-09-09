from datetime import datetime

from sqlalchemy import TIMESTAMP, VARCHAR, Column
from sqlmodel import Field


class LockableMixin:
    """
    Mixin that adds a lockable feature to a model, allowing it to be locked after multiple failed login attempts.

    Attributes:
        failed_attempts (int): Number of failed login attempts.
        unlock_token (str | None): Token used to unlock the account.
        locked_at (datetime | None): Timestamp when the account was locked.
    """

    failed_attempts: int = Field(
        default=0,
        nullable=False,
    )

    unlock_token: str | None = Field(
        sa_column=Column(
            VARCHAR(length=128),
            default=None,
            unique=True,
            nullable=True,
        )
    )

    locked_at: datetime | None = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=True,
            default=None,
        )
    )
