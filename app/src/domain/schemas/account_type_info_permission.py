from datetime import datetime

from pydantic import BaseModel
from src.core.helpers.schema import optional
from src.core.types import GUID


class AccountTypeInfoPermissionBase(BaseModel):
    """Base schema for AccountTypeInfoPermission."""

    account_type_info_id: GUID
    permission_id: int
    granted: bool = True
    resource_id: str | None = None
    assigned_by: GUID | None = None
    expires_at: datetime | None = None


class AccountTypeInfoPermissionCreate(AccountTypeInfoPermissionBase):
    """Schema for creating account type info permission."""

    pass


@optional
class AccountTypeInfoPermissionUpdate(AccountTypeInfoPermissionBase):
    """Schema for updating account type info permission."""

    pass


class AccountTypeInfoPermissionResponse(AccountTypeInfoPermissionBase):
    """Schema for account type info permission responses."""

    id: GUID
    assigned_at: datetime

    class Config:
        from_attributes = True
