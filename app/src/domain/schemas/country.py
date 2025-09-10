from uuid import UUID

from pycountries import Country as CountryEnum
from pycountries import Language
from pydantic import BaseModel, field_validator
from src.core.helpers.schema import optional


class CountryBase(BaseModel):
    """Base schema for Country."""

    name: CountryEnum
    language: Language
    currency_id: UUID
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_country_name(cls, v: CountryEnum) -> CountryEnum:
        """Validate that the country name is valid."""
        if not v:
            raise ValueError("Country name is required")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Language) -> Language:
        """Validate that the language is valid."""
        if not v:
            raise ValueError("Language is required")
        return v


class CountryCreate(CountryBase):
    """Schema for creating a country."""

    pass


@optional
class CountryUpdate(CountryCreate):
    """Schema for updating a country."""

    pass


class CountryResponse(CountryBase):
    """Schema for country responses."""

    id: str  # UUID as string

    class Config:
        from_attributes = True
