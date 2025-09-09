from datetime import datetime

from sqlalchemy import TEXT, TIMESTAMP, Column
from sqlmodel import Field


class ConfirmableMixin:
    """
    Mixin that adds a confirmation token and its expiration to a model.

    Attributes\n:
        confirmation_token (str | None): Token used for confirming the record.
        confirmation_token_expires_at (datetime | None): Expiration time for the confirmation token.
        email_confirmed (bool): Indicates whether the email has been confirmed.
        confirmed_at (datetime | None): Timestamp when the email was confirmed.
    """

    email_confirmed: bool = Field(
        default=False,
        nullable=False,
    )

    confirmed_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=True,
        default=None,
    )

    confirmation_token: str = Field(sa_column=Column(TEXT(), nullable=True, default=None, unique=True))

    confirmation_token_sent_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=True,
        default=None,
    )
