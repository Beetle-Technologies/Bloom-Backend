from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from pydantic import EmailStr
from sqlalchemy import TEXT, TIMESTAMP, Column, ColumnElement, Index, String, func, type_coerce
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import Field, Relationship
from src.core.config import settings
from src.core.database.mixins import (
    AuthenticatableMixin,
    ConfirmableMixin,
    DeletableMixin,
    FriendlyMixin,
    GUIDMixin,
    LockableMixin,
    RecoverableMixin,
    RememberableMixin,
    SearchableMixin,
    TimestampMixin,
    TrackableMixin,
)
from src.core.types import IDType, PhoneNumber
from src.domain.enums import AccountTypeEnum

if TYPE_CHECKING:
    from src.domain.models import AccountType, AccountTypeInfo, ProductItemRequest


class Account(
    GUIDMixin,
    FriendlyMixin,
    AuthenticatableMixin,
    LockableMixin,
    TrackableMixin,
    RememberableMixin,
    ConfirmableMixin,
    RecoverableMixin,
    SearchableMixin,
    TimestampMixin,
    DeletableMixin,
    table=True,
):
    """
    Represents an account in the system.

    Attributes:\n
        id (GUID): The unique identifier for the account.
        friendly_id (str | None): A url-friendly identifier for the account.
        first_name (str): The first name of the account.
        last_name (str): The last name of the account.
        email (EmailStr): The email address of the account.
        username (str | None): The username of the account.
        phone_number (PhoneNumber | None): The phone number of the account.
        encrypted_password (str): The encrypted password of the account.
        password_salt (str): The salt used for encrypting the password.
        is_active (bool): Indicates whether the account is active.
        is_verified (bool): Indicates whether the account has verified their email.
        is_suspended (bool): Indicates whether the account is suspended.
        suspended_datetime (datetime | None): The datetime when the account was suspended.
        suspended_reason (str | None): The reason for the account's suspension.
        failed_attempts (int): The number of failed login attempts.
        unlock_token (str | None): A token used to unlock the account after suspension.
        locked_at (datetime | None): The datetime when the account was locked.
        password_reset_token (str | None): A token used for password reset.
        password_reset_token_created_at (datetime | None): The datetime when the password reset token was created.
        email_confirmed (bool): Indicates whether the email has been confirmed.
        confirmed_at (datetime | None): The timestamp when the email was confirmed.
        confirmation_token (str | None): Token used for confirming the record.
        confirmation_token_sent_at (datetime | None): The datetime when the confirmation token was sent.
        remember_token (str | None): A token used to remember the user.
        remember_token_created_at (datetime | None): The datetime when the remember token was created.
        search_text (str | None): A concatenated string of searchable fields for full-text search.
        search_vector (str | None): A search vector for full-text search capabilities.
        sign_in_count (int): The number of times the user has signed in.
        current_sign_in_at (datetime | None): The timestamp of the current sign-in.
        last_sign_in_at (datetime | None): The timestamp of the last sign-in.
        current_sign_in_ip (str | None): The IP address of the current sign-in.
        last_sign_in_ip (str | None): The IP address of the last sign-in.
        last_password_change_at (datetime | None): The datetime when the password was last changed.
        last_sign_in_user_agent (str | None): The user agent of the last sign-in
        created_datetime (datetime): The timestamp when the account was created.
        updated_datetime (datetime | None): The timestamp when the account was last updated.
        deleted_datetime (datetime | None): The timestamp when the account was deleted.
    """

    __table_args__ = (Index("idx_account_search_vector", "search_vector", postgresql_using="gin"),)

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "friendly_id",
        "first_name",
        "last_name",
        "email",
        "username",
        "account_type",
        "phone_number",
        "is_active",
        "is_verified",
        "is_suspended",
        "suspended_datetime",
        "suspended_reason",
        "email_confirmed",
        "confirmed_at",
        "sign_in_count",
        "current_sign_in_at",
        "last_sign_in_at",
        "current_sign_in_ip",
        "last_sign_in_ip",
        "last_sign_in_user_agent",
        "created_datetime",
        "updated_datetime",
        "deleted_datetime",
        "type_attributes",
    ]

    first_name: str
    last_name: str
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    username: str | None = Field(index=True, unique=True, default=None)
    phone_number: PhoneNumber | None = Field(
        sa_column=Column(
            TEXT(),
            nullable=True,
            default=None,
        )
    )

    is_active: bool = Field(
        default=True,
        nullable=False,
    )
    is_verified: bool = Field(
        default=False,
        nullable=False,
    )
    is_suspended: bool = Field(
        default=False,
        nullable=False,
    )
    suspended_datetime: datetime | None = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=True,
            default=None,
        )
    )
    suspended_reason: str | None = Field(
        sa_column=Column(
            TEXT(),
            nullable=True,
            default=None,
        )
    )

    # Relationships
    type_infos: list["AccountTypeInfo"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[AccountTypeInfo.account_id]",
            "lazy": "selectin",
            "back_populates": "account",
        }
    )

    account_types: list["AccountType"] = Relationship(
        sa_relationship_kwargs={
            "secondary": "account_type_infos",
            "back_populates": "accounts",
            "viewonly": True,
        }
    )

    # Product item request relationships
    resale_requests_as_seller: list["ProductItemRequest"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ProductItemRequest.seller_account_id]",
            "back_populates": "seller",
        }
    )
    resale_requests_as_supplier: list["ProductItemRequest"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ProductItemRequest.supplier_account_id]",
            "back_populates": "supplier",
        }
    )

    # Properties
    display_name: ClassVar = hybrid_property(lambda self: f"{self.first_name.title()} {self.last_name.title()}")

    @display_name.inplace.setter
    def _display_name_setter(self, value: str):
        """
        Sets the user's first and last name from a full name string.
        """
        if " " not in value:
            raise ValueError("Display name must contain both first and last names.")
        self.first_name, self.last_name = value.split(" ", 1)

    @display_name.inplace.expression
    def _display_name_expression(cls) -> ColumnElement[str]:
        """
        SQL expression for the display name property.
        """
        return type_coerce(
            func.concat(func.initcap(cls.first_name), " ", func.initcap(cls.last_name)),
            String(),
        ).label("display_name")

    # Methods
    def check_password(self, plain_password: str) -> bool:
        """
        Verifies the provided plain password against the encrypted password.
        """
        from src.core.security import verify_password

        return verify_password(plain_password, self.encrypted_password, self.password_salt)

    def check_suspended(self) -> bool:
        """
        Checks if the user account is currently suspended.
        """
        return self.is_suspended and (self.suspended_datetime is not None)

    def is_locked(self) -> bool:
        """
        Checks if the user account is currently locked.
        """
        return self.locked_at is not None

    def is_eligible_for_login(self) -> bool:
        """
        Checks if the user account is prevented from logging in.
        """
        return self.check_suspended() or self.is_locked() or not self.is_active or not self.is_verified

    def check_reenumeration_attempts(self) -> bool:
        """
        Checks if the user account has exceeded the maximum number of failed login attempts.
        """
        if self.is_locked() and self.failed_attempts >= settings.MAX_LOGIN_FAILED_ATTEMPTS:
            return True

        return False

    def has_permission(
        self,
        permission_scope: str,
        account_type: AccountTypeEnum | None = None,
        resource_id: IDType | None = None,
    ) -> bool:
        """
        Check if the account has a specific permission for a given account type.

        Args:
            permission_scope: The permission scope (e.g., 'users:read')
            account_type: The account type to check permissions for. If None, checks all account types.
            resource_id: Optional resource ID for resource-specific permissions

        Returns:
            True if the permission is granted and active, False otherwise
        """
        for type_info in self.type_infos:
            if account_type is None or type_info.account_type == account_type:
                if type_info.has_permission(permission_scope, resource_id):
                    return True
        return False

    def get_permissions_for_account_type(self, account_type: AccountTypeEnum) -> list[str]:
        """
        Get all permission scopes for a specific account type.

        Args:
            account_type: The account type to get permissions for

        Returns:
            List of permission scopes
        """
        for type_info in self.type_infos:
            if type_info.account_type.key == account_type.value:
                return type_info.get_permission_scopes()
        return []

    def get_all_permissions(self) -> dict[AccountTypeEnum, list[str]]:
        """
        Get all permissions for all account types associated with this account.

        Returns:
            Dictionary mapping account types to their permission scopes
        """
        permissions = {}
        for type_info in self.type_infos:
            permissions[AccountTypeEnum(type_info.account_type.key)] = type_info.get_permission_scopes()
        return permissions

    def get_account_type_infos(self, account_type: AccountTypeEnum) -> "AccountTypeInfo | None":
        """
        Get the account type attribute for a specific account type.

        Args:
            account_type: The account type to get attributes for

        Returns:
            AccountType | None: The AccountTypeInfo instance or None if not found
        """
        for type_info in self.type_infos:
            if type_info.account_type.key == account_type.value:
                return type_info
        return None

    def has_account_type(self, account_type: AccountTypeEnum) -> bool:
        """
        Check if the account has a specific account type.

        Args:
            account_type: The account type to check for

        Returns:
            True if the account has this account type, False otherwise
        """
        return self.get_account_type_infos(account_type) is not None

    def get_account_types(self) -> list[AccountTypeEnum]:
        """
        Get all account types associated with this account.

        Returns:
            List of AccountType enums
        """
        return [AccountTypeEnum(type_info.account_type.key) for type_info in self.type_infos]

    def get_active_account_types(self) -> list[AccountTypeEnum]:
        """
        Get all active account types associated with this account.
        This method can be extended later if account type infos have active/inactive states.

        Returns:
            List of AccountType enums for active account types
        """
        # For now, all account type infos are considered active
        # This can be extended later with additional filtering logic
        return self.get_account_types()
