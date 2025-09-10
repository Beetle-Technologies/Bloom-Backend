from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar, Optional

from sqlalchemy import TIMESTAMP, Column, UniqueConstraint, func
from sqlmodel import Field, Relationship
from src.core.database.mixins import UUIDMixin
from src.core.types import GUID

if TYPE_CHECKING:
    from src.domain.models import Account, AccountTypeInfo, Permission


class AccountTypeInfoPermission(UUIDMixin, table=True):
    """
    Represents the permissions associated with an account type attribute.

    This allows for flexible permission management where different account types
    can have different permissions, and an account can have multiple account type
    attributes with their own set of permissions.

    Attributes:\n
        id (int): Unique identifier for the account type permission.
        account_type_info_id (UUID): The ID of the account type attribute this permission belongs to.
        permission_id (int): The ID of the permission.
        granted (bool): Indicates whether the permission is granted or denied.
        resource_id (str | None): The ID of the resource this permission applies to, if any.
        assigned_at (datetime): The timestamp when the permission was assigned.
        assigned_by (UUID | None): The ID of the account that assigned this permission.
        expires_at (datetime | None): The timestamp when the permission expires, if applicable.
    """

    __tablename__ = "account_type_permissions"  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "account_type_info_id",
            "permission_id",
            "resource_id",
            name="uq_account_type_permission",
        ),
    )

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "account_type_info_id",
        "permission_id",
        "granted",
        "resource_id",
        "assigned_at",
        "assigned_by",
        "expires_at",
    ]

    account_type_info_id: GUID = Field(foreign_key="account_type_infos.id", nullable=False, index=True)
    permission_id: int = Field(foreign_key="permissions.id", nullable=False, index=True)

    granted: bool = Field(default=True, nullable=False)
    resource_id: str | None = Field(default=None, max_length=255)
    assigned_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    assigned_by: GUID | None = Field(default=None, foreign_key="accounts.id")
    expires_at: datetime | None = Field(default=None)

    # Relationships
    account_type_info: Optional["AccountTypeInfo"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[AccountTypeInfoPermission.account_type_info_id]",
            "back_populates": "permissions",
        }
    )

    permission: Optional["Permission"] = Relationship()

    assigned_by_account: Optional["Account"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[AccountTypeInfoPermission.assigned_by]",
        }
    )

    def is_active(self) -> bool:
        """
        Check if the permission is currently active (not expired).

        Returns:
            True if the permission is active, False otherwise
        """
        if self.expires_at is None:
            return True
        return datetime.now(UTC) < self.expires_at

    def is_granted_and_active(self) -> bool:
        """
        Check if the permission is both granted and active.

        Returns:
            True if the permission is granted and active, False otherwise
        """
        return self.granted and self.is_active()
