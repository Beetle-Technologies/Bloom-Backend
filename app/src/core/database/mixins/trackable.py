from datetime import datetime

from sqlalchemy import TEXT, TIMESTAMP, VARCHAR, Column
from sqlmodel import Field


class TrackableMixin:
    """
    Mixin to add tracking fields to SQLModel classes.

    Attributes:\n
        sign_in_count (int): Number of times the user has signed in.
        current_sign_in_at (datetime | None): Timestamp of the current sign-in.
        last_sign_in_at (datetime | None): Timestamp of the last sign-in.
        last_password_change_at (datetime | None): Timestamp of the last password change.
        current_sign_in_ip (str | None): IP address of the current sign-in.
        last_sign_in_ip (str | None): IP address of the last sign-in.
        last_sign_in_user_agent (str | None): User agent string of the current sign-in.
    """

    sign_in_count: int = Field(
        default=0,
        nullable=False,
    )
    current_sign_in_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=True,
        default=None,
    )
    last_sign_in_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=True,
        default=None,
    )
    last_password_change_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=True,
        default=None,
    )
    current_sign_in_ip: str | None = Field(sa_column=Column(VARCHAR(length=16), nullable=True, default=None))
    last_sign_in_ip: str | None = Field(sa_column=Column(VARCHAR(length=16), nullable=True, default=None))
    last_sign_in_user_agent: str | None = Field(sa_column=Column(TEXT(), nullable=True, default=None))
