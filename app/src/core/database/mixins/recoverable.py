from datetime import datetime

from sqlalchemy import TIMESTAMP, VARCHAR, Column
from sqlmodel import Field


class RecoverableMixin:
    """
    Mixin for models that resets for `encrypted_password`

    Attributes:\n
        password_reset_token (str | None): Token used for password reset.
        password_reset_token_expires_at (datetime | None): Expiration time for the password reset token.
    """

    password_reset_token: str | None = Field(
        sa_column=Column(
            VARCHAR(length=128),
            default=None,
            nullable=True,
        )
    )

    password_reset_token_created_at: datetime | None = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            default=None,
            nullable=True,
        )
    )
