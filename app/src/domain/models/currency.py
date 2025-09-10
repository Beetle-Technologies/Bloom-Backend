from typing import TYPE_CHECKING, ClassVar

from babel.numbers import get_currency_symbol
from pycountries import Currency as CurrencyCode
from sqlalchemy import VARCHAR, Boolean, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import UUIDMixin

if TYPE_CHECKING:
    from src.domain.models import Country


class Currency(UUIDMixin, table=True):
    """
    Represents a currency in the system.

    Attributes:\n
        id (UUID): The unique identifier for the currency.
        code (str): The ISO 4217 currency code (e.g., USD, EUR).
        symbol (str): The symbol of the currency (e.g., $).
        is_active (bool): Indicates whether the currency is active.
        is_default (bool): Indicates whether this currency is the default one.
        countries (list[Country]): The list of countries that use this currency.
    """

    __tablename__ = "currency"  # type: ignore

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "code",
        "is_active",
        "is_default",
    ]

    code: CurrencyCode = Field(
        description="ISO 4217 currency code (e.g., USD, EUR)",
        sa_column=Column(VARCHAR(), unique=True, index=True),
    )
    is_active: bool = Field(
        sa_column=Column(type_=Boolean(), default=True, nullable=False),
        description="Indicates if the currency is active",
    )
    is_default: bool = Field(
        sa_column=Column(type_=Boolean(), default=False, nullable=False),
        description="Indicates if this currency is the default one for the system",
    )
    countries: list["Country"] = Relationship(back_populates="currency", sa_relationship_kwargs={"lazy": "selectin"})

    @property
    def symbol(self) -> str:
        code = self.code.value

        try:
            symbol = get_currency_symbol(code)
            return symbol
        except Exception:
            return code
