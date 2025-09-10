from pycountries import Currency as CurrencyCode
from pydantic import BaseModel, field_validator
from src.core.helpers.schema import optional


class CurrencyBase(BaseModel):
    """Base schema for Currency."""

    code: CurrencyCode
    is_active: bool = True
    is_default: bool = False

    @field_validator("code")
    @classmethod
    def validate_currency_code(cls, v: CurrencyCode) -> CurrencyCode:
        """Validate that the currency code is valid."""
        if not v:
            raise ValueError("Currency code is required")
        return v


class CurrencyCreate(CurrencyBase):
    """Schema for creating a currency."""

    pass


@optional
class CurrencyUpdate(CurrencyCreate):
    """Schema for updating a currency."""

    pass


class CurrencyResponse(CurrencyBase):
    """Schema for currency responses."""

    id: str  # UUID as string
    symbol: str

    class Config:
        from_attributes = True
