from sqlalchemy import TEXT, Column
from sqlmodel import Field


class AuthenticatableMixin:
    """
    Mixin that adds authentication features to a model, allowing it to be authenticated using a password.

    Attributes:\n
       encrypted_password (str): The encrypted password of the user.
       password_salt (str): The salt used for encrypting the password.
    """

    encrypted_password: str = Field(
        sa_column=Column(
            TEXT(),
            nullable=False,
        )
    )
    password_salt: str = Field(
        sa_column=Column(
            TEXT(),
            nullable=False,
        )
    )
