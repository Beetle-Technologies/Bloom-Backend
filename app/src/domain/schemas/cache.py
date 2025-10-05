from pydantic import BaseModel, EmailStr


class CachedAccountData(BaseModel):
    """
    Represents cached account data for pre-check validation.

    Attributes:
        email (EmailStr): The email address of the account.
        username (str | None): The username of the account.
    """

    email: EmailStr
    friendly_id: str | None = None
    username: str | None = None
