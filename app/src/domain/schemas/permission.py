from pydantic import BaseModel, field_validator
from src.core.helpers.schema import optional


class PermissionBase(BaseModel):
    """Base schema for Permission."""

    resource: str
    action: str
    description: str | None = None

    @field_validator("resource", "action")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that resource and action are not empty strings."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip().lower()


class PermissionCreate(PermissionBase):
    """Schema for creating a permission."""

    pass


@optional
class PermissionUpdate(PermissionCreate):
    """Schema for updating a permission."""

    pass


class PermissionResponse(PermissionBase):
    """Schema for permission responses."""

    id: int
    scope: str

    class Config:
        from_attributes = True
