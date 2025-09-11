from typing import Any, Dict

from pydantic import BaseModel, Field
from src.core.helpers.schema import optional
from src.core.types import GUID


class AccountTypeInfoBase(BaseModel):
    """Base schema for AccountTypeInfo."""

    account_id: GUID
    account_type_id: GUID
    attributes: Dict[str, Any] = Field(default_factory=dict)


class AccountTypeInfoCreate(AccountTypeInfoBase):
    """Schema for creating account type info."""

    pass


@optional
class AccountTypeInfoUpdate(AccountTypeInfoBase):
    """Schema for updating account type info."""

    pass


class AccountTypeInfoResponse(AccountTypeInfoBase):
    """Schema for account type info responses."""

    id: GUID

    class Config:
        from_attributes = True
