from datetime import datetime

from sqlalchemy import TEXT, TIMESTAMP, Column
from sqlmodel import Field


class RememberableMixin:
    """
    Mixin that adds a remember token to the model.

    Attributes:
        remember_token (str | None): Token used to remember the user.
        remember_token_expires_at (datetime | None): Expiration time for the remember token.
    """

    remember_token: str | None = Field(sa_column=Column(TEXT(), nullable=True, unique=True))

    remember_token_created_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=True,
        default=None,
    )
