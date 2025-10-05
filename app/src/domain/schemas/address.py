from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from src.core.helpers.misc import call
from src.core.helpers.schema import optional
from src.core.types import GUID, PhoneNumber
from src.domain.schemas.country import CountryBasicResponse


class AddressBase(BaseModel):
    """Base schema for Address."""

    phone_number: PhoneNumber | None = Field(None, description="Phone number associated with the address")
    address: str = Field(..., min_length=1, max_length=500, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(..., min_length=1, max_length=100, description="State or province")
    postal_code: str | None = Field(None, max_length=20, description="Postal or ZIP code")
    is_default: bool = Field(default=False, description="Whether this is the default address")


class AddressCreate(AddressBase):
    """Schema for creating an address."""

    country_id: UUID = Field(..., description="ID of the country")
    addressable_type: str = Field(..., description="Type of the related object")
    addressable_id: GUID = Field(..., description="ID of the related object")


@optional
class AddressUpdate(AddressBase):
    """Schema for updating an address."""

    country_id: UUID | None = Field(None, description="ID of the country")


class AddressResponse(AddressBase):
    """Schema for address responses."""

    fid: str | None = Field(None, description="User-friendly identifier for the address")
    country: CountryBasicResponse | None = None
    created_datetime: datetime = Field(..., description="When the address was created")
    updated_datetime: datetime | None = Field(None, description="When the address was last updated")

    @classmethod
    def from_obj(cls, obj: Any) -> "AddressResponse":
        data = cls(
            fid=getattr(obj, "friendly_id", None),
            phone_number=getattr(obj, "phone_number", None),
            address=getattr(obj, "address", ""),
            city=getattr(obj, "city", ""),
            state=getattr(obj, "state", ""),
            postal_code=getattr(obj, "postal_code", None),
            is_default=getattr(obj, "is_default", False),
            created_datetime=getattr(obj, "created_datetime"),
            updated_datetime=getattr(obj, "updated_datetime"),
        )

        if call(obj, "country"):
            data.country = CountryBasicResponse(
                id=obj.country.id,
                name=obj.country.name,
                is_active=obj.country.is_active,
            )

        return data


class AddressCreateRequest(BaseModel):
    """Schema for address creation request."""

    phone_number: PhoneNumber | None = Field(None, description="Phone number associated with the address")
    address: str = Field(..., min_length=1, max_length=500, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(..., min_length=1, max_length=100, description="State or province")
    postal_code: str | None = Field(None, max_length=20, description="Postal or ZIP code")
    country_id: UUID = Field(..., description="ID of the country")
    is_default: bool = Field(default=False, description="Whether this is the default address")


class AddressUpdateRequest(BaseModel):
    """Schema for address update request."""

    phone_number: PhoneNumber | None = Field(None, description="Phone number associated with the address")
    address: str | None = Field(None, min_length=1, max_length=500, description="Street address")
    city: str | None = Field(None, min_length=1, max_length=100, description="City name")
    state: str | None = Field(None, min_length=1, max_length=100, description="State or province")
    postal_code: str | None = Field(None, max_length=20, description="Postal or ZIP code")
    country_id: UUID | None = Field(None, description="ID of the country")
    is_default: bool | None = Field(None, description="Whether this is the default address")
