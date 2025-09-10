from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from sqlalchemy import TEXT
from sqlmodel import Boolean, Column, Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID, PhoneNumber

if TYPE_CHECKING:
    from src.domain.models.country import Country


class Address(GUIDMixin, TimestampMixin, table=True):
    """
    Represents an address in the system.

    Attributes:\n
        id (UUID): The unique identifier for the address.
        phone_number (PhoneNumber | None): The phone number associated with the address.
        address (str): The street address.
        city (str): The city of the address.
        state (str): The state of the address.
        postal_code (str | None): The postal code of the address.
        is_default (bool): Indicates if this address is the default address for the account.
        created_datetime (datetime): The timestamp when the address was created.
        updated_datetime (datetime | None): The timestamp when the address was last updated.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "phone_number",
        "address",
        "city",
        "state",
        "postal_code",
        "is_default",
        "created_datetime",
        "updated_datetime",
    ]

    addressable_type: str = Field(
        max_length=120,
        nullable=False,
        index=True,
        description="Type of the related object (e.g., 'AccountTypeInfo', 'Order')",
    )
    addressable_id: GUID = Field(
        nullable=False,
        index=True,
        description="ID of the related object (GUID)",
    )

    country_id: UUID = Field(foreign_key="country.id", nullable=False)

    phone_number: PhoneNumber | None = Field(
        sa_column=Column(
            TEXT(),
            default=None,
            nullable=True,
            index=True,
        ),
    )
    address: str = Field(
        sa_column=Column(
            TEXT(),
            nullable=False,
        ),
    )
    city: str = Field(
        sa_column=Column(
            TEXT(),
            nullable=False,
        ),
    )
    state: str = Field(
        sa_column=Column(
            TEXT(),
            nullable=False,
        ),
    )
    is_default: bool = Field(
        sa_column=Column(
            default=False,
            type_=Boolean(),
            nullable=False,
        ),
    )
    postal_code: str | None = Field(
        sa_column=Column(
            TEXT(),
            default=None,
            nullable=True,
        ),
    )

    # Relationships
    country: "Country" = Relationship(
        back_populates="addresses",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
