from typing import TYPE_CHECKING

from pydantic import JsonValue
from sqlalchemy import TEXT, Boolean, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import KYCDocumentVerificationStatus

if TYPE_CHECKING:
    from src.domain.models import Account, KYCDocumentType


class KYCDocument(GUIDMixin, TimestampMixin, table=True):
    """
    A KYC document model representing a unique document submission by an account for a
    specific document type, ensuring each account has only one record per document type.
    """

    __tablename__ = "kyc_documents"  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "document_type_id",
            name="uq_kyc_document__account_id__document_type_id",
        ),
    )

    SELECTABLE_FIELDS = [
        "id",
        "account_id",
        "document_type_id",
        "attachment_id",
        "value",
        "status",
        "extra_data",
        "created_datetime",
        "updated_datetime",
    ]

    account_id: GUID = Field(foreign_key="accounts.id", nullable=False)
    document_type_id: GUID = Field(foreign_key="kyc_document_types.id", nullable=False)
    attachment_id: GUID = Field(foreign_key="attachments.id", nullable=False)
    value: str | None = Field(
        sa_column=Column(TEXT(), nullable=True),
        description="Optional value submitted with the document",
    )
    status: KYCDocumentVerificationStatus = Field(nullable=False)
    attributes: JsonValue = Field(
        sa_column=Column(JSONB, nullable=True, default=None),
    )

    # Relationships
    account: "Account" = Relationship()
    document_type: "KYCDocumentType" = Relationship()
    verification_comments: list["KYCDocumentVerificationComment"] = Relationship(
        back_populates="kyc_document"
    )


class KYCDocumentVerificationComment(GUIDMixin, TimestampMixin, table=True):
    """
    Represents comments made during KYC document verification process.

    Attributes:
        id (GUID): Unique identifier for the comment.
        kyc_document_id (GUID): ID of the KYC document associated with the comment.
        reviewer_account_id (GUID): ID of the account that reviewed the document.
        content (str): Content of the comment.
        is_internal (bool): Indicates if the comment is internal or external.
        created_datetime (datetime): Timestamp when the comment was created.
        updated_datetime (datetime | None): Timestamp when the comment was last updated.
    """

    __tablename__ = "kyc_document_verification_comments"  # type: ignore

    SELECTABLE_FIELDS = [
        "id",
        "kyc_document_id",
        "reviewer_account_id",
        "content",
        "is_internal",
        "created_datetime",
        "updated_datetime",
    ]

    kyc_document_id: GUID = Field(foreign_key="kyc_documents.id", nullable=False)
    reviewer_account_id: GUID = Field(foreign_key="accounts.id", nullable=False)
    content: str = Field(sa_column=Column(TEXT(), nullable=False))
    is_internal: bool = Field(
        sa_column=Column(Boolean(), nullable=False, default=False),
        description="Whether this comment is internal or visible to the account",
    )

    # Relationships
    kyc_document: "KYCDocument" = Relationship(back_populates="verification_comments")
    reviewer: "Account" = Relationship()
