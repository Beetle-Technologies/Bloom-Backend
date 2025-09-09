from typing import TYPE_CHECKING
from uuid import UUID

from pycountries import Country as CountryEnum
from pycountries import Language
from sqlalchemy import TEXT, Boolean, Column
from sqlmodel import Field, Relationship
from src.core.database.mixins import UUIDMixin

if TYPE_CHECKING:
    from src.domain.models import Currency


class Country(UUIDMixin, table=True):
    """
    Represents a country with its ISO 3166-1 alpha-2 code and associated currency.

    Attributes:\n
        id (UUID): Unique identifier for the country.
        name (str): Name of the country.
        currency_id (UUID): Foreign key referencing the associated currency.
        is_active (bool): Indicates if the country is active.
    """

    __tablename__ = "country"  # type: ignore

    name: CountryEnum = Field(sa_column=Column(TEXT(), unique=True))
    language: Language = Field(
        sa_column=Column(TEXT()), description="Primary language spoken in the country"
    )

    currency_id: UUID = Field(foreign_key="currency.id")
    currency: "Currency" = Relationship(
        back_populates="countries",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    is_active: bool = Field(
        sa_column=Column(type_=Boolean(), default=True, nullable=False)
    )
