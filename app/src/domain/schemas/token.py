from datetime import datetime

from pydantic import BaseModel
from src.core.helpers.schema import optional
from src.core.types import GUID


class TokenBase(BaseModel):
    """Base schema for Token."""

    token: str
    revoked: bool = False


class TokenCreate(TokenBase):
    """Schema for creating a token."""

    deleted_datetime: datetime


@optional
class TokenUpdate(TokenBase):
    """Schema for updating a token."""

    pass


class TokenResponse(TokenBase):
    """Schema for token responses."""

    id: GUID

    class Config:
        from_attributes = True
