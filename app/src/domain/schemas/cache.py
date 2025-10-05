from pydantic import BaseModel, EmailStr
from src.core.types import GUID


class CachedAccountData(BaseModel):
    """
    Represents cached account data for pre-check validation.

    Attributes:
        email (EmailStr): The email address of the account.
        username (str | None): The username of the account.
    """

    id: GUID
    friendly_id: str | None = None
    email: EmailStr
    username: str | None = None
