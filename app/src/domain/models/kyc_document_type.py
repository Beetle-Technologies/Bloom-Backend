from typing import TYPE_CHECKING

from pydantic import JsonValue
from sqlalchemy import TEXT, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import AccountTypeEnum, KYCVerificationType

if TYPE_CHECKING:
    from src.domain.models import Country


class KYCDocumentType(GUIDMixin, TimestampMixin, table=True):
    """
    Represents a type of KYC document with unique constraints based on name,
    """

    __tablename__ = "kyc_document_types"  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "name",
            "country_id",
            "account_type",
            name="uq_kyc_document_type__name__country__account_type",
        ),
    )

    SELECTABLE_FIELDS = [
        "id",
        "name",
        "is_active",
        "account_type",
        "verification_type",
        "country_id",
        "additional_info",
        "created_datetime",
        "updated_datetime",
    ]

    name: str = Field(max_length=255, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    account_type: AccountTypeEnum = Field()
    verification_type: KYCVerificationType = Field(
        sa_column=Column(TEXT(), nullable=False, default=KYCVerificationType.MANUAL)
    )
    country_id: GUID = Field(foreign_key="country.id", nullable=False)

    requires_value_submission: bool = Field(
        default=False,
        description="Indicates if the document type requires the user to submit a value with the file submission.",
    )

    attributes: JsonValue = Field(
        sa_column=Column(JSONB, nullable=True, default={}),
    )

    # Relationships
    country: "Country" = Relationship()
