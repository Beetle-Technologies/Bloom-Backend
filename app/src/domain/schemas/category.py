from pydantic import BaseModel, Field
from src.core.helpers.schema import optional
from src.core.types import GUID


class CategoryBase(BaseModel):
    """Base category schema with common fields"""

    title: str = Field(..., max_length=255, description="The title of the category")
    description: str | None = Field(None, description="Description of the category")
    parent_id: GUID | None = Field(None, description="Reference to parent category")
    is_active: bool = Field(True, description="Whether the category is active")
    sort_order: int = Field(0, description="Sort order for display")


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""

    pass


@optional
class CategoryUpdate(CategoryBase):
    """Schema for updating a category"""

    pass


class CategoryResponse(CategoryBase):
    """Schema for category response"""

    id: GUID = Field(..., description="The unique identifier for the category")
    friendly_id: str = Field(..., description="A URL-friendly identifier for the category")

    class Config:
        from_attributes = True
