from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import IDType
from src.domain.models.account import Account
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import AccountCreate, AccountUpdate
from src.domain.services.security_service import security_service

logger = get_logger(__name__)


class AccountRepository(BaseRepository[Account, AccountCreate, AccountUpdate]):
    """
    Repository for managing accounts in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Account, session)

    async def get_by_email(self, email: str) -> Account | None:
        """Get account by email address."""
        try:
            return await self.find_one_by_or_none(email=email)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.account_repository.get_by_email:: error while getting account by email {email}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve account",
                detail="An error occurred while retrieving account.",
                metadata={"email": email},
            ) from e

    async def get_by_username(self, username: str) -> Account | None:
        """Get account by username."""
        try:
            return await self.find_one_by_or_none(username=username)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.account_repository.get_by_username:: error while getting account by username {username}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve account",
                detail="An error occurred while retrieving account.",
                metadata={"username": username},
            ) from e

    async def get_by_friendly_id(self, friendly_id: str) -> Account | None:
        """Get account by friendly ID."""
        try:
            return await self.find_one_by_or_none(friendly_id=friendly_id)
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.account_repository.get_by_friendly_id:: error while getting account by friendly_id {friendly_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve account",
                detail="An error occurred while retrieving account.",
                metadata={"friendly_id": friendly_id},
            ) from e

    async def get_active_accounts(self) -> Sequence[Account]:
        """Get all active accounts."""
        try:
            query = select(Account).filter(
                col(Account.is_active) == True,  # noqa: E712
                col(Account.deleted_datetime).is_(None),  # noqa: E712
            )
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.account_repository.get_active_accounts:: error while getting active accounts: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve active accounts",
                detail="An error occurred while retrieving active accounts.",
            ) from e

    async def get_verified_accounts(self) -> Sequence[Account]:
        """Get all verified accounts."""
        try:
            query = select(Account).filter(
                col(Account.is_verified) == True,  # noqa: E712
                col(Account.deleted_datetime).is_(None),
            )
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.account_repository.get_verified_accounts:: error while getting verified accounts: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to retrieve verified accounts",
                detail="An error occurred while retrieving verified accounts.",
            ) from e

    async def create_account(self, account: AccountCreate) -> Account:
        """
        Create a new account.

        Args:
            account (AccountCreate): The data for the new account.

        Returns:
            Account: The created account object.
        """
        try:
            hashed_password, salt = security_service.hash_password(password=account.password)

            new_account = Account(
                email=account.email,
                username=account.username,
                first_name=account.first_name,
                last_name=account.last_name,
                phone_number=str(account.phone_number),
                encrypted_password=hashed_password,  # type: ignore[assignment]
                password_salt=salt,  # type: ignore[assignment]
                is_active=True,
                is_verified=True,
                is_suspended=False,
            )
            new_account.save_friendly_fields()
            self.session.add(new_account)
            await self._save_changes(new_account)

            return new_account
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.account_repository.create_account:: error while creating account: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to create account",
                detail="An error occurred while creating the account.",
            ) from e

    async def update_last_sign_in(self, id: IDType, ip_address: str, user_agent: str) -> bool:
        """
        Update last sign-in information for an account.

        Args:
            account_id (UUID): The ID of the account to update.
            ip_address (str): The IP address of the user signing in.
            user_agent (str): The user agent string of the user's device.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            account = await self.find_one_by(id)
            if not account:
                return False

            account.sqlmodel_update(
                {
                    "last_sign_in_at": account.current_sign_in_at,
                    "last_sign_in_ip": account.current_sign_in_ip,
                    "current_sign_in_at": datetime.now(UTC),
                    "current_sign_in_ip": ip_address,
                    "last_sign_in_user_agent": user_agent,
                    "sign_in_count": account.sign_in_count + 1,
                }
            )
            self.session.add(account)
            await self._save_changes(account)
            return True
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.account_repository.update_last_sign_in:: error while updating last sign-in for account {id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to update account",
                detail="An error occurred while updating your account.",
                metadata={"id": id, "action": "update_last_sign_in"},
            ) from e

    async def soft_delete(self, account_id: IDType) -> bool:  # type: ignore
        """
        Schedules a deletion of an account.

        Args:
            account_id (UUID): The ID of the account to soft delete.

        Returns:
            bool: True if the account was successfully soft deleted, False otherwise.
        """
        try:
            account = await self.find_one_by(account_id)
            if not account:
                return False

            account.sqlmodel_update({"deleted_datetime": datetime.now(UTC), "is_active": False})
            self.session.add(account)
            await self._save_changes(account)
            return True
        except SQLAlchemyError as e:
            logger.exception(
                f"src.domain.repositories.account_repository.soft_delete:: error while soft deleting account {account_id}: {e}"
            )
            raise errors.DatabaseError(
                message="Failed to delete account",
                detail="An error occurred while deleting the account.",
                metadata={"id": account_id, "action": "soft_delete"},
            ) from e
