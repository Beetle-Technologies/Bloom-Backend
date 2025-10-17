from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from src.core.helpers import optional
from src.core.types import GUID


class StoreColorsBase(BaseModel):
    """Base schema for store color configuration."""

    primary: str = Field(..., description="Primary color (hex)")
    secondary: str = Field(..., description="Secondary color (hex)")
    accent: str = Field(..., description="Accent color (hex)")
    surface: str = Field(..., description="Surface color (hex)")
    background: str = Field(..., description="Background color (hex)")
    text: str = Field(..., description="Text color (hex)")


class StoreTypographyBase(BaseModel):
    """Base schema for store typography configuration."""

    display_font: str = Field(..., description="Display font family")
    body_font: str = Field(..., description="Body font family")


class StoreSpacingBase(BaseModel):
    """Base schema for store spacing configuration."""

    radius: str = Field(..., description="Border radius value")
    container_padding: str = Field(..., description="Container padding value")


class StoreBrandingBase(BaseModel):
    """Base schema for store branding configuration."""

    pass


class StoreThemeBase(BaseModel):
    """Base schema for store theme configuration."""

    id: str = Field(..., description="Theme identifier")
    name: str = Field(..., description="Theme display name")
    colors: StoreColorsBase
    typography: StoreTypographyBase
    spacing: StoreSpacingBase
    branding: StoreBrandingBase


class StoreShippingBase(BaseModel):
    """Base schema for store shipping configuration."""

    enabled: bool = Field(default=True, description="Whether shipping is enabled")
    free_shipping_threshold: Optional[Decimal] = Field(None, description="Minimum amount for free shipping")
    zones: List[str] = Field(default_factory=list, description="Available shipping zones")


class StorePaymentBase(BaseModel):
    """Base schema for store payment configuration."""

    methods: List[str] = Field(default_factory=list, description="Available payment methods")
    currency: str = Field(default="USD", description="Default currency")
    tax_included: bool = Field(default=False, description="Whether tax is included in prices")


class StoreFeaturesBase(BaseModel):
    """Base schema for store features configuration."""

    reviews: bool = Field(default=True, description="Enable product reviews")
    wishlist: bool = Field(default=True, description="Enable wishlist functionality")
    compare: bool = Field(default=True, description="Enable product comparison")
    guest_checkout: bool = Field(default=True, description="Allow guest checkout")
    multi_currency: bool = Field(default=False, description="Enable multi-currency support")
    inventory: bool = Field(default=True, description="Enable inventory tracking")


class StoreSettingsBase(BaseModel):
    """Base schema for store settings configuration."""

    currency: str = Field(default="USD", description="Store currency")
    locale: str = Field(default="en-US", description="Store locale")
    timezone: str = Field(default="America/New_York", description="Store timezone")
    shipping: StoreShippingBase
    payment: StorePaymentBase
    features: StoreFeaturesBase


class StoreMetadataBase(BaseModel):
    """Base schema for store metadata."""

    title: str = Field(..., description="Store title")
    description: str = Field(..., description="Store description")
    keywords: List[str] = Field(default_factory=list, description="SEO keywords")


class StoreBase(BaseModel):
    """Base store schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Store name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly store identifier")
    description: Optional[str] = Field(None, description="Store description")
    theme: StoreThemeBase
    settings: StoreSettingsBase
    metadata: StoreMetadataBase

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        import re

        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v


class StoreCreate(StoreBase):
    """Schema for creating a new store."""

    owner_account_id: GUID = Field(..., description="ID of the account that owns this store")


@optional
class StoreUpdate(StoreBase):
    """Schema for updating a store."""

    pass


class StoreResponse(StoreBase):
    """Schema for store response data."""

    id: GUID
    friendly_id: Optional[str]
    owner_account_id: GUID
    is_active: bool = Field(default=True, description="Whether the store is active")
    is_public: bool = Field(default=False, description="Whether the store is publicly visible")
    created_datetime: str
    updated_datetime: Optional[str]
    deleted_datetime: Optional[str]


class StoreBasicResponse(BaseModel):
    """Schema for basic store information."""

    id: GUID
    fid: str = Field(..., description="Friendly ID of the store")
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    is_public: bool


class StoreColorsCreate(StoreColorsBase):
    """Schema for creating store colors."""

    pass


@optional
class StoreColorsUpdate(StoreColorsBase):
    """Schema for updating store colors."""

    pass


class StoreThemeCreate(StoreThemeBase):
    """Schema for creating store theme."""

    pass


@optional
class StoreThemeUpdate(StoreThemeBase):
    """Schema for updating store theme."""

    pass


class StoreSettingsCreate(StoreSettingsBase):
    """Schema for creating store settings."""

    pass


@optional
class StoreSettingsUpdate(StoreSettingsBase):
    """Schema for updating store settings."""

    pass
