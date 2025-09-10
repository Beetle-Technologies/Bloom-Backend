from sqlmodel import Field
from src.core.database.mixins import DeletableMixin, UUIDMixin


class Token(UUIDMixin, DeletableMixin, table=True):
    """
    Represents a token used for authentication or other purposes.

    Attributes:
        id (UUID): The unique identifier for the token.
        token (str): The token string.
        revoked (bool): Indicates whether the token has been revoked.
        deleted_datetime (datetime): The timestamp when the token will be deleted, if applicable.
    """

    token: str = Field(index=True, unique=True, nullable=False)
    revoked: bool = Field(default=False, index=True)
