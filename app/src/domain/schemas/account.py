from __future__ import annotations

from datetime import datetime
from typing import Optional, Self

from pydantic import BaseModel, EmailStr, Field, JsonValue, model_validator
from src.core.helpers import optional
from src.core.types import GUID, Password, PhoneNumber


class AuthAccount(BaseModel):
    """
    Schema representing an account in the authentication context.

    Attributes:\n
        id (GUID): Unique identifier for the account.
        friendly_id (str): A unique identifier for the account, typically a username or a unique string.
        username (str | None): The account's username, if available.
        email (EmailStr): The account's email address.
        display_name (str): The account's display name, which may differ from the username.
        avatar (str | None): URL to the account's avatar image, if available.
    """

    id: GUID
    friendly_id: str | None
    email: EmailStr
    username: str
    display_name: str


class AccountBase(BaseModel):
    """Base account schema with common fields."""

    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    username: str | None = Field(None, min_length=3, max_length=255, pattern=r"^[a-zA-Z0-9_.-]+$")
    phone_number: PhoneNumber | None = None


class AccountCreate(AccountBase):
    """Schema for creating a new account."""

    password: Password


@optional
class AccountUpdate(AccountBase):

    type_attributes: JsonValue | None = None


class AccountResponse(BaseModel):
    """Schema for account response data."""

    id: GUID
    friendly_id: Optional[str]
    first_name: str
    last_name: str
    email: EmailStr
    username: str
    phone_number: PhoneNumber | None
    is_active: bool
    is_verified: bool
    is_suspended: bool
    locked_at: datetime | None = None
    email_confirmed: bool


class AccountPasswordUpdate(BaseModel):
    """Schema for updating account password."""

    current_password: Password
    new_password: Password
    confirm_new_password: Password

    @model_validator(mode="after")
    def validate_passwords_match(self) -> Self:
        password = self.new_password
        confirm_password = self.confirm_new_password

        if password != confirm_password:
            raise ValueError("Passwords do not match")

        return self


class AccountTypeCreate(BaseModel):
    """Schema for creating a new account type."""

    title: str = Field(..., min_length=1, max_length=120)
    key: str = Field(..., min_length=1, max_length=64)


@optional
class AccountTypeUpdate(AccountTypeCreate):
    """Schema for updating an existing account type."""

    pass


class AccountBasicProfileResponse(BaseModel):
    """Schema for account profile response data."""

    fid: str = Field(..., description="Unique friendly identifier for the account")
    first_name: str
    last_name: str
    email: EmailStr
    username: str | None
    phone_number: PhoneNumber | None
    attachment: Optional[str] = Field(None, description="URL to the profile attachment")
    is_active: bool
    is_verified: bool
    is_suspended: bool
    locked_at: datetime | None = None
    type_attributes: JsonValue = Field(..., description="Attributes related to the account type")
