from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import TEXT, TIMESTAMP, Boolean, Column, ColumnElement, String, type_coerce
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import Field, Relationship, col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.domain.enums import BankAccountType, BankingInfoStatus
from src.domain.services import security_service

if TYPE_CHECKING:
    from src.domain.models import AccountTypeInfo


BANKING_INFO_ENCRYPTION_CONTEXT = settings.BANKING_SECRET_KEY


class BankingInfo(GUIDMixin, TimestampMixin, table=True):
    """
    Represents banking information for an account with encrypted sensitive data.

    Attributes:
        id (GUID): The unique identifier for the banking info.
        account_id (GUID): ID of the account that owns this banking info.
        account_type_info_id (GUID | None): Optional ID of the specific account type info this banking info is for.
        bank_name (str): Name of the bank.
        account_holder_name (str): Name of the account holder.
        encrypted_account_number (str): Encrypted bank account number.
        encrypted_routing_number (str | None): Encrypted bank routing number (optional).
        bank_account_type (BankAccountType): Type of bank account.
        bank_address (str | None): Address of the bank.
        swift_code (str | None): SWIFT/BIC code for international transfers.
        status (BankingInfoStatus): Current status of the banking info.
        is_primary (bool): Whether this is the primary banking info for the account.
        is_verified (bool): Whether this banking info has been verified.
        verified_at (datetime | None): When the banking info was verified.
        is_active (bool): Whether this banking info is active.
        nickname (str | None): Optional nickname for this banking info.
        created_datetime (datetime): When the banking info was created.
        updated_datetime (datetime | None): When the banking info was last updated.
    """

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "account_id",
        "account_type_info_id",
        "bank_name",
        "account_holder_name",
        "account_type",
        "bank_address",
        "swift_code",
        "status",
        "is_primary",
        "is_verified",
        "verified_at",
        "is_active",
        "nickname",
        "created_datetime",
        "updated_datetime",
    ]

    # Foreign key relationships
    account_type_info_id: GUID = Field(
        foreign_key="account_type_infos.id",
        nullable=False,
        index=True,
        description="Optional specific account type info this banking info is associated with",
    )

    # Bank information
    bank_name: str = Field(max_length=255, nullable=False)
    account_holder_name: str = Field(max_length=255, nullable=False)

    # Encrypted sensitive fields
    encrypted_account_number: str = Field(sa_column=Column(TEXT(), nullable=False))
    encrypted_routing_number: str | None = Field(sa_column=Column(TEXT(), nullable=True))

    # Account details
    bank_account_type: BankAccountType = Field(
        default=BankAccountType.CHECKING,
        nullable=False,
        description="Type of bank account",
    )
    bank_address: str | None = Field(sa_column=Column(TEXT(), nullable=True))
    swift_code: str | None = Field(
        max_length=11,
        nullable=True,
        description="SWIFT/BIC code for international transfers",
    )

    # Status fields
    status: BankingInfoStatus = Field(sa_column=Column(TEXT(), default=BankingInfoStatus.PENDING, nullable=False))
    is_primary: bool = Field(sa_column=Column(Boolean(), default=False, nullable=False))
    is_verified: bool = Field(sa_column=Column(Boolean(), default=False, nullable=False))
    verified_at: datetime | None = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=True,
            default=None,
        )
    )
    is_active: bool = Field(default=True, nullable=False)

    # Optional fields
    nickname: str | None = Field(
        max_length=100,
        nullable=True,
        description="Optional nickname for easy identification",
    )

    # Relationships
    account_type_info: "AccountTypeInfo" = Relationship(back_populates="banking_infos")

    @classmethod
    def _get_cipher(cls):
        """Get the encryption cipher for banking data."""
        return security_service.get_cryptographic_signer(BANKING_INFO_ENCRYPTION_CONTEXT)

    @classmethod
    def encrypt_account_number(cls, account_number: str) -> str:
        """Encrypt a bank account number."""
        cipher = cls._get_cipher()
        return cipher.encrypt(account_number.encode()).decode()

    @classmethod
    def encrypt_routing_number(cls, routing_number: str) -> str:
        """Encrypt a bank routing number."""
        cipher = cls._get_cipher()
        return cipher.encrypt(routing_number.encode()).decode()

    def decrypt_account_number(self) -> str:
        """Decrypt the bank account number."""
        cipher = self._get_cipher()
        return cipher.decrypt(self.encrypted_account_number.encode()).decode()

    def decrypt_routing_number(self) -> str | None:
        """Decrypt the bank routing number."""
        if self.encrypted_routing_number is None:
            return None
        cipher = self._get_cipher()
        return cipher.decrypt(self.encrypted_routing_number.encode()).decode()

    # Properties
    masked_account_number: ClassVar = hybrid_property(
        lambda self: (
            "****"
            if (decrypted := self.decrypt_account_number()) is None
            else ("*" * len(decrypted) if len(decrypted) <= 4 else "*" * (len(decrypted) - 4) + decrypted[-4:])
        )
    )

    @masked_account_number.inplace.expression
    def _masked_account_number_expression(cls) -> ColumnElement[str]:
        """SQL expression for masked account number (returns '****' for security)."""
        return type_coerce(cls.masked_account_number, String()).label("masked_account_number")

    masked_routing_number: ClassVar = hybrid_property(
        lambda self: (
            "N/A"
            if (decrypted := self.decrypt_routing_number()) is None
            else ("*" * len(decrypted) if len(decrypted) <= 4 else "*" * (len(decrypted) - 4) + decrypted[-4:])
        )
    )

    @masked_routing_number.inplace.expression
    def _masked_routing_number_expression(cls) -> ColumnElement[str]:
        """SQL expression for masked routing number (returns 'N/A' if not set)."""
        return type_coerce(cls.masked_routing_number, String()).label("masked_routing_number")

    @classmethod
    def create_with_encryption(
        cls,
        bank_name: str,
        account_holder_name: str,
        account_number: str,
        routing_number: str | None,
        bank_account_type: BankAccountType,
        **kwargs,
    ) -> "BankingInfo":
        """
        Create a new BankingInfo instance with encrypted sensitive data.

        Args:
            bank_name: Name of the bank
            account_holder_name: Name of the account holder
            account_number: Plain text account number (will be encrypted)
            routing_number: Plain text routing number (will be encrypted)
            account_type: Type of bank account
            **kwargs: Additional optional fields

        Returns:
            BankingInfo instance with encrypted sensitive data
        """
        klass = cls(
            bank_name=bank_name,
            account_holder_name=account_holder_name,
            encrypted_account_number=cls.encrypt_account_number(account_number),
            bank_account_type=bank_account_type,
            **kwargs,
        )

        if routing_number:
            klass.encrypted_routing_number = cls.encrypt_routing_number(routing_number)

        return klass

    def update_account_number(self, new_account_number: str) -> None:
        """Update the account number with a new encrypted value."""
        self.encrypted_account_number = self.encrypt_account_number(new_account_number)

    def update_routing_number(self, new_routing_number: str | None) -> None:
        """Update the routing number with a new encrypted value."""
        if new_routing_number is None:
            self.encrypted_routing_number = None
        else:
            self.encrypted_routing_number = self.encrypt_routing_number(new_routing_number)

    def to_safe_dict(self) -> dict:
        """
        Return a dictionary representation with sensitive data masked.
        Useful for API responses or logging.
        """
        return {
            "id": str(self.id),
            "account_type_info_id": (str(self.account_type_info_id) if self.account_type_info_id else None),
            "bank_name": self.bank_name,
            "account_holder_name": self.account_holder_name,
            "masked_account_number": self.masked_account_number,
            "masked_routing_number": self.masked_routing_number,
            "bank_account_type": self.bank_account_type.value,
            "bank_address": self.bank_address,
            "swift_code": self.swift_code,
            "status": self.status.value,
            "is_primary": self.is_primary,
            "is_verified": self.is_verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "is_active": self.is_active,
            "nickname": self.nickname,
            "created_datetime": self.created_datetime.isoformat(),
            "updated_datetime": (self.updated_datetime.isoformat() if self.updated_datetime else None),
        }

    @classmethod
    async def get_banking_info_for_account_type(
        cls,
        session: AsyncSession,
        account_type_info_id: GUID,
        banking_info_id: GUID | None = None,
    ) -> "BankingInfo | None":
        """
        Get banking info for a specific account type info, or fallback to primary banking info.

        Args:
            account_id (GUID): The account ID to get banking info for
            account_type_info_id (GUID): Optional specific account type info ID
            session: Database session (should be provided from calling context)

        Returns:
            BankingInfo instance or None if not found
        """
        if session is None:
            raise ValueError("Session must be provided")

        banking_info: BankingInfo | None = None

        if banking_info_id:
            banking_info = (
                await session.exec(
                    select(cls).filter(
                        col(cls.id) == banking_info_id,  # noqa: E712
                        col(cls.account_type_info_id) == account_type_info_id,  # noqa: E712
                        col(cls.is_active) == True,  # noqa: E712
                    )
                )
            ).one_or_none()

            if banking_info:
                return banking_info

        banking_info = (
            await session.exec(
                select(cls).filter(
                    col(cls.account_type_info_id) == account_type_info_id,  # noqa: E712
                    col(cls.is_active) == True,  # noqa: E712
                )
            )
        ).one_or_none()

        return banking_info

    def is_associated_with_account_type(self, account_type_info_id: GUID) -> bool:
        """
        Check if this banking info is associated with a specific account type info.

        Args:
            account_type_info_id: The account type info ID to check

        Returns:
            True if associated, False otherwise
        """
        return self.account_type_info_id == account_type_info_id
