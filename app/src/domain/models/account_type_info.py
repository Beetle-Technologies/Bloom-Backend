from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID, IDType
from src.domain.models.account_type import AccountType

if TYPE_CHECKING:
    from src.domain.models import (
        Account,
        AccountTypeInfoPermission,
        Address,
        Attachment,
        BankingInfo,
        Cart,
        Notification,
        Order,
        Review,
        Wishlist,
    )


class AccountTypeInfo(GUIDMixin, TimestampMixin, table=True):
    """
    Represents dynamic attributes for different account types stored as JSONB.

    This model allows for flexible storage of account-specific attributes based on account type.
    For example:
    - Business accounts might have: tax_id, business_license, industry_code
    - Supplier accounts might have: certifications, delivery_areas, product_categories
    - User accounts might have: preferences, loyalty_points, subscription_tier

    Attributes:\n
        id (UUID): The unique identifier for the account type attribute.
        account_id (UUID): The ID of the account these attributes belong to.
        account_type (AccountType): The type of account these attributes are for.
        attributes (Dict[str, Any]): JSONB field containing dynamic attributes.
        created_datetime (datetime): The timestamp when the attributes were created.
        updated_datetime (datetime | None): The timestamp when the attributes were last updated.
    """

    __tablename__ = "account_type_infos"  # type: ignore

    __table_args__ = (
        UniqueConstraint("account_id", "account_type_id", name="uq_account_type_info_account_type"),
        Index("idx_account_type_infos_account_type", "account_id", "account_type_id"),
        Index(
            "idx_account_type_infos_attributes",
            "attributes",
            postgresql_using="gin",
        ),
    )

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "account_id",
        "account_type_id",
        "attachment_id",
        "attributes",
        "created_datetime",
        "updated_datetime",
    ]

    account_id: GUID = Field(foreign_key="accounts.id", nullable=False, index=True)
    account_type_id: GUID = Field(foreign_key="account_types.id", nullable=False, index=True)
    attachment_id: Optional[GUID] = Field(foreign_key="attachments.id", nullable=True, index=True)

    attributes: Dict[str, Any] = Field(
        sa_column=Column(
            JSONB,
            nullable=False,
            default=dict,
        ),
        description="JSONB field containing dynamic attributes specific to the account type",
    )

    # Relationships
    account: "Account" = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "back_populates": "type_infos",
        }
    )

    account_type: "AccountType" = Relationship(back_populates="type_infos")

    attachment: Optional["Attachment"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "primaryjoin": "Attachment.id == AccountTypeInfo.attachment_id",
            "foreign_keys": "[AccountTypeInfo.attachment_id]",
            "uselist": False,
        }
    )

    permissions: list["AccountTypeInfoPermission"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[AccountTypeInfoPermission.account_type_info_id]",
            "back_populates": "account_type_info",
            "lazy": "selectin",
        }
    )
    banking_infos: list["BankingInfo"] = Relationship(
        back_populates="account_type_info", sa_relationship_kwargs={"lazy": "selectin"}
    )

    carts: list["Cart"] = Relationship(
        back_populates="account_type_info",
        sa_relationship_kwargs={
            "foreign_keys": "[Cart.account_type_info_id]",
            "lazy": "selectin",
        },
    )

    notifications: list["Notification"] = Relationship(
        back_populates="account_type_info",
        sa_relationship_kwargs={
            "foreign_keys": "[Notification.account_type_info_id]",
            "lazy": "selectin",
        },
    )

    orders: list["Order"] = Relationship(
        back_populates="account_type_info",
        sa_relationship_kwargs={
            "foreign_keys": "[Order.account_type_info_id]",
            "lazy": "selectin",
        },
    )

    wishlists: list["Wishlist"] = Relationship(
        back_populates="account_type_info",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    reviews: list["Review"] = Relationship(back_populates="account_type_info")

    addresses: list["Address"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Address.addressable_type == 'AccountTypeInfo' and Address.addressable_id == AccountTypeInfo.id",
            "lazy": "selectin",
        }
    )

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """
        Get a specific attribute value from the JSONB field.

        Args:
            key (str): The attribute key to retrieve
            default (Any): Default value if key doesn't exist

        Returns:
            The attribute value or default
        """
        return self.attributes.get(key, default)

    def set_attribute(self, key: str, value: Any) -> None:
        """
        Set a specific attribute value in the JSONB field.

        Args:
            key (str): The attribute key to set
            value (Any): The value to set
        """
        if self.attributes is None:
            self.attributes = {}
        self.attributes[key] = value

    def remove_attribute(self, key: str) -> Any:
        """
        Remove a specific attribute from the JSONB field.

        Args:
            key (str): The attribute key to remove

        Returns:
            The removed value or None if key didn't exist
        """
        if self.attributes is None:
            return None
        return self.attributes.pop(key, None)

    def has_attribute(self, key: str) -> bool:
        """
        Check if a specific attribute exists in the JSONB field.

        Args:
            key (str): The attribute key to check

        Returns:
            True if the attribute exists, False otherwise
        """
        return self.attributes is not None and key in self.attributes

    def update_attributes(self, new_attributes: Dict[str, Any]) -> None:
        """
        Update multiple attributes at once.

        Args:
            new_attributes (Dict[str, Any]): Dictionary of attributes to update
        """
        if self.attributes is None:
            self.attributes = {}
        self.attributes.update(new_attributes)

    def has_permission(self, permission_scope: str, resource_id: IDType | None = None) -> bool:
        """
        Check if this account type attribute has a specific permission.

        Args:
            permission_scope (str): The permission scope (e.g., 'users:read')
            resource_id (str | None): Optional resource ID for resource-specific permissions

        Returns:
            True if the permission is granted and active, False otherwise
        """
        for permission in self.permissions:
            if (
                permission.permission
                and permission.permission.scope == permission_scope
                and permission.resource_id == resource_id
                and permission.is_granted_and_active()
            ):
                return True
        return False

    def get_permissions(self, active_only: bool = True) -> list["AccountTypeInfoPermission"]:
        """
        Get all permissions for this account type attribute.

        Args:
            active_only (bool): If True, only return active (non-expired) permissions

        Returns:
            list[str]: List of permissions
        """
        if active_only:
            return [p for p in self.permissions if p.is_granted_and_active()]
        return self.permissions

    def get_permission_scopes(self, active_only: bool = True) -> list[str]:
        """
        Get all permission scopes for this account type attribute.

        Args:
            active_only (bool): If True, only return scopes for active permissions

        Returns:
            list[str]: List of permission scopes
        """
        permissions = self.get_permissions(active_only)

        allowed_permissions_scopes: list[str] = []

        for p in permissions:
            if p.permission:
                allowed_permissions_scopes.append(p.permission.scope)

        return allowed_permissions_scopes

    def get_banking_info(self, active_only: bool = True) -> "BankingInfo | None":
        """
        Get the banking info associated with this account type info.

        Args:
            active_only: If True, only return active banking info

        Returns:
            BankingInfo instance or None if not found
        """
        for banking_info in self.banking_infos:
            if not active_only or banking_info.is_active:
                return banking_info
        return None

    def has_banking_info(self, active_only: bool = True) -> bool:
        """
        Check if this account type info has associated banking info.

        Args:
            active_only: If True, only consider active banking info

        Returns:
            True if banking info exists, False otherwise
        """
        return self.get_banking_info(active_only) is not None
