from typing import Annotated, Literal, Self

import email_validator
from pydantic import BaseModel, EmailStr, Field, JsonValue, StringConstraints, model_validator
from src.core.types import GUID, Password, PhoneNumber
from src.domain.enums import AccountTypeEnum, AuthPreCheckTypeEnum, TokenVerificationRequestTypeEnum


class AuthPreCheckRequest(BaseModel):
    """
    Represents a request to pre-check an email or username

    Attributes:
        type (AuthPreCheckTypeEnum): The type of pre-check to perform (e.g., EMAIL, USERNAME).
        value (str): The email or username to check.
        mode (Literal["register", "login"]): The mode of the pre-check, either "register" or "login".
    """

    type: AuthPreCheckTypeEnum = AuthPreCheckTypeEnum.EMAIL
    value: Annotated[str, StringConstraints(min_length=1, max_length=255, strip_whitespace=True)]
    mode: Literal["register", "login"] = "register"

    @model_validator(mode="after")
    def validate_value(self) -> Self:
        if self.type == AuthPreCheckTypeEnum.EMAIL:
            try:
                email_validator.validate_email(self.value)
            except email_validator.EmailNotValidError as e:
                raise ValueError(f"Invalid email address: {e}") from e

        if self.type == AuthPreCheckTypeEnum.USERNAME and self.mode == "login":
            raise ValueError("Username pre-check is only allowed in register mode.")

        return self


class AuthRegisterRequest(BaseModel):
    """
    Represents a request to register a new account.

    Attributes:
        first_name (str): The first name of the account holder.
        last_name (str): The last name of the account holder.
        phone_number (PhoneNumber | None): The phone number of the account holder.
        email (EmailStr): The email address of the account.
        password (Password): The password for the account.
    """

    first_name: Annotated[str, StringConstraints(min_length=1, max_length=255, strip_whitespace=True)]
    last_name: Annotated[str, StringConstraints(min_length=1, max_length=255, strip_whitespace=True)]
    email: EmailStr
    password: Password
    phone_number: PhoneNumber | None = None
    type_attributes: JsonValue | None = None


class AuthVerificationTokenRequest(BaseModel):
    """
    Represents a request to generate an authentication token.
    """

    email: EmailStr
    mode: TokenVerificationRequestTypeEnum = TokenVerificationRequestTypeEnum.OTP
    is_resend: bool = False


class AuthSessionToken(BaseModel):
    """
    Represents an authentication session token.

    Attributes:
        scope (Literal["access", "refresh"]): The scope of the token, either "access" or "refresh".
        token (str): The authentication token.
        expires_in (int): The expiration time of the token in seconds.
    """

    scope: Literal["access", "refresh"]
    token: str
    expires_in: int


class AuthRegisterResponse(BaseModel):
    """
    Represents the response returned after a successful registration.

    Attributes:
        fid (str): The friendly identifier for the account.
        is_verified (bool): Indicates if the account is verified.
    """

    fid: str = Field(..., description="The friendly identifier for the account")
    is_verified: bool = Field(False, description="Indicates if the account is verified")


class AuthSessionResponse(BaseModel):
    """
    Represents the response returned after a successful authentication.

    Attributes:
        tokens (list[AuthSessionToken]): A list of authentication session tokens.
    """

    tokens: list[AuthSessionToken]


class AuthSessionState(BaseModel):
    """
    Represents the authentication state of a account.

    Attributes:
        id (GUID): The unique identifier for the account.
        type_info_id (GUID): The identifier for the type information associated with the account.
        type (AccountTypeEnum): The type of the account (e.g., ADMIN, USER
    """

    id: GUID
    type_info_id: GUID
    type: AccountTypeEnum
