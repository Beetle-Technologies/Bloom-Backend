from typing import Annotated, Literal, Self

import email_validator
from pydantic import BaseModel, EmailStr, Field, JsonValue, StringConstraints, computed_field, model_validator
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


class AuthVerificationRequest(BaseModel):
    """
    Represents a request to generate an authentication token.
    """

    fid: str = Field(..., description="The friendly identifier for the account")
    mode: TokenVerificationRequestTypeEnum = TokenVerificationRequestTypeEnum.OTP


class AuthTokenVerificationRequest(BaseModel):
    """
    Represents a request to verify an authentication token.

    Attributes:
        token (str): The authentication token to verify.
        mode (TokenVerificationRequestTypeEnum): The mode of the token verification, either "OTP" or "STATE_KEY".
    """

    token: str = Field(..., description="The authentication token to verify")
    mode: TokenVerificationRequestTypeEnum = TokenVerificationRequestTypeEnum.OTP


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


class AuthPreCheckResponse(BaseModel):
    """
    Represents the response for a pre-check request.

    Attributes:
        exists (bool): Whether the email/username exists in the system.
        is_verified (bool): Whether the account is verified (if exists).
        can_login (bool): Whether the account can login (only for login mode).
        source (str): The source of the data ("cache" or "database").
    """

    exists: bool
    is_verified: bool
    fid: str | None = Field(None, description="The friendly identifier for the account (if exists)")
    can_login: bool = Field(..., description="Whether the account can login (only for login mode)")


class AuthLogoutRequest(BaseModel):
    """
    Represents a request to logout an account.

    Attributes:
        access_token (str): The access token to be invalidated.
        refresh_token (str): The refresh token to be invalidated.
    """

    access_token: str = Field(..., description="The access token to be invalidated")
    refresh_token: str | None = Field(..., description="The refresh token to be invalidated")


class AuthTokenRefreshRequest(AuthLogoutRequest):
    """
    Represents a request to refresh authentication tokens.

    Attributes:
        access_token (str): The current access token.
        refresh_token (str): The current refresh token.
    """

    pass


class AuthForgotPasswordRequest(BaseModel):
    """
    Represents a request to initiate a password reset process.

    Attributes:
        email (EmailStr): The email address associated with the account.
    """

    email: EmailStr = Field(..., description="The email address associated with the account")


class AuthPasswordResetRequest(BaseModel):
    """
    Represents a request to reset the password of an account.

    Attributes:
        token (str): The password reset token.
        new_password (Password): The new password for the account.
        confirm_new_password (Password): Confirmation of the new password.
    """

    token: str = Field(..., description="The password reset token")
    new_password: Password = Field(..., description="The new password for the account")
    confirm_new_password: Password = Field(..., description="Confirmation of the new password")

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.new_password != self.confirm_new_password:
            raise ValueError("New password and confirmation do not match.")
        return self


class AuthPasswordChangeRequest(BaseModel):
    """
    Represents a request to change the password of an authenticated account.

    Attributes:
        current_password (Password): The current password of the account.
        new_password (Password): The new password for the account.
        confirm_new_password (Password): Confirmation of the new password.
    """

    current_password: Password = Field(..., description="The current password of the account")
    new_password: Password = Field(..., description="The new password for the account")
    confirm_new_password: Password = Field(..., description="Confirmation of the new password")

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.new_password != self.confirm_new_password:
            raise ValueError("New password and confirmation do not match.")
        return self


class AuthUserSessionRequest(BaseModel):
    """
    Represents a request to create an authentication session for a user account type

    Attributes:
        first_name (str | None): The first name of the user.
        last_name (str | None): The last name of the user.
        email (EmailStr): The email address of the account.
        otp (str | None): The one-time password (OTP) for authentication.
    """

    first_name: str | None = Field(..., description="The first name of the user")
    last_name: str | None = Field(..., description="The last name of the user")
    email: EmailStr = Field(..., description="The email address of the account")
    otp: str | None = Field(None, description="The one-time password (OTP) for authentication")
    mode: Literal["register", "trigger_login", "login"] = "login"

    @model_validator(mode="after")
    def validate_mode(self) -> Self:
        if self.mode == "register":
            if not (self.first_name and self.last_name and self.email and self.otp):
                raise ValueError("For registration, first name, last name, email, and OTP are required.")
        if self.mode == "trigger_login":
            if not self.email:
                raise ValueError("For triggering login, email is required.")
        elif self.mode == "login":
            if not (self.email and self.otp):
                raise ValueError("For login, email and OTP are required.")
        else:
            raise ValueError("Mode must be either 'register' or 'login'.")
        return self

    @computed_field
    @property
    def password(self) -> Password | None:
        from src.domain.services.security_service import security_service

        # Here I just generate a default deterministic password for the user if first and last name, email are provided else None
        password_key = f"{self.first_name}{self.last_name}{self.email}"
        return (
            security_service.generate_deterministic_password(password_key)
            if self.first_name and self.last_name and self.email
            else None
        )


class AuthUserSessionResponse(BaseModel):
    """
    Represents the response returned after a successful user session creation.

    Attributes:
        token (AuthSessionToken): The authentication session token.
    """

    token: AuthSessionToken = Field(..., description="The authentication access session token")
