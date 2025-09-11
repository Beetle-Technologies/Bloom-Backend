from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import status
from pydantic import EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.exceptions import errors
from src.core.types import IDType, Password, PhoneNumber
from src.domain.models import Account
from src.domain.repositories import AccountRepository
from src.domain.schemas import AccountCreate, AccountUpdate
from src.domain.services.security_service import security_service

logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_repository = AccountRepository(session=self.session)

    async def get_account_by(self, **kwargs) -> Account | None:
        """
        Get user by email address.

        Args:
            keywords: Arbitrary keyword arguments to filter the account.

        Returns:
            Account | None: The account if found, otherwise None.
        """
        return await self.account_repository.find_one_by_or_none(**kwargs)

    async def create_account(
        self,
        *,
        first_name: str,
        last_name: str,
        email: EmailStr,
        password: Password,
        username: str | None,
        phone_number: PhoneNumber | None,
    ) -> Account:
        """
        Create a new user account.

        Args:
            first_name (str): The first name of the user.
            last_name (str): The last name of the user.
            username (str | None): The username of the user (optional).
            email (EmailStr): The email address of the user.
            password (Password): The password of the user.
            phone_number (PhoneNumber | None): The phone number of the user (optional).

        Returns:
            Account: The created account.
        """
        try:
            existing_account = await self.account_repository.find_one_by_and_none(email=email, username=username)

            if existing_account:
                raise errors.AccountAlreadyExistsError()

            account_data = AccountCreate(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password,
                phone_number=phone_number,
            )
            return await self.account_repository.create(account_data)
        except errors.DatabaseError as de:
            logger.exception(
                f"src.domain.services.account_service.create_account:: error while creating account for {email}: {de!s}",
            )
            raise errors.AccountCreationError(
                detail="Failed to create account",
            ) from de
        except errors.ServiceError as se:
            raise se

    async def authenticate(
        self,
        *,
        email: EmailStr,
        password: Password,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Account:
        """
        Authenticate a user by email and password.

        Args:
            email (EmailStr): The email address of the user.
            password (Password): The password of the user.
            ip_address (str | None): The IP address of the user.
            user_agent (str | None): The user agent of the user.

        Returns:
            Account: The authenticated account if successful, otherwise None.
        """

        try:
            account = await self.account_repository.get_by_email(email)
            if not account or account.deleted_datetime is not None:
                raise errors.AccountNotFoundError()

            if account.is_eligible():
                raise errors.AccountIneligibleError(
                    metadata={
                        "verified": account.is_verified,
                        "suspended": account.is_suspended,
                        "locked": account.is_locked(),
                    },
                )

            if account.check_reenumeration_attempts():
                if account.locked_at and (datetime.now(UTC) - account.locked_at) < timedelta(
                    seconds=settings.MAX_LOGIN_RETRY_TIME
                ):
                    raise errors.AccountLockedError()
                else:
                    account.locked_at = None
                    account.failed_attempts = 0

            if not account.check_password(password):
                account.failed_attempts += 1

                if account.failed_attempts >= settings.MAX_LOGIN_FAILED_ATTEMPTS:
                    account.locked_at = datetime.now(UTC)
                    account.unlock_token = security_service.generate_random_token()

            account.failed_attempts = 0
            account.locked_at = None
            account.sign_in_count += 1
            account.last_sign_in_at = account.current_sign_in_at
            account.last_sign_in_ip = account.current_sign_in_ip
            account.current_sign_in_at = datetime.now(UTC)
            account.current_sign_in_ip = ip_address
            account.last_sign_in_user_agent = user_agent

            await self.account_repository.update(account.id, account)

            return account
        except errors.DatabaseError as de:
            logger.exception(
                f"src.domain.services.account_service.authenticate:: error while authenticating account with email {email}: {de}"
            )
            raise errors.AuthenticationError(
                detail="Failed to authenticate account.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from de
        except errors.ServiceError as se:
            raise se

    async def update_password(self, id: IDType, current_password: Password, new_password: Password) -> Account:
        """
        Update account password.

        Args:
            account_id (UUID): The ID of the account to update.
            current_password (Password): The current password of the account.
            new_password (Password): The new password to set for the account.

        Returns:
            Account: The updated account with the new password.
        """

        try:
            account = await self.account_repository.find_one_by(id)
            if not account:
                raise errors.AccountNotFoundError()

            if current_password == new_password:
                raise errors.AccountChangePasswordMismatchError()

            if not account.check_password(current_password):
                raise errors.AccountInvalidPasswordError()

            hashed_password, salt = security_service.hash_password(password=new_password)

            await self.account_repository.update(
                account.id,
                {
                    "encrypted_password": hashed_password,
                    "password_salt": salt,
                    "last_password_change_at": datetime.now(UTC),
                },
            )
            return account
        except errors.DatabaseError as de:
            logger.exception(
                f"src.domain.repositories.account_repository.update_password:: error while updating password for account {id}: {de!s}",
            )
            raise errors.AccountUpdateError(
                detail="Failed to update password for account",
            ) from de
        except errors.ServiceError as se:
            raise se

    async def request_password_reset(self, email: EmailStr) -> str:
        """
        Request a password reset for an account.

        Args:
            email (EmailStr): The email address of the account.

        Returns:
            str: The password reset token if the request was successful.
        """
        try:
            account = await self.get_account_by(email=email)
            if not account:
                raise errors.AccountNotFoundError()

            password_reset_token = security_service.generate_random_token()

            await self.account_repository.update(
                account.id,
                AccountUpdate(
                    password_reset_token=password_reset_token,
                    password_reset_token_created_at=datetime.now(UTC),
                ),
            )

            return password_reset_token
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.account_service.request_password_reset:: error while requesting password reset for {email}: {e}",
            )
            raise errors.AccountUpdateError(
                detail="Failed to request password reset",
            ) from e
        except errors.ServiceError as se:
            logger.exception(
                f"src.domain.services.account_service.request_password_reset:: error while requesting password reset for {email}: {se}",
            )
            raise se

    async def reset_account_password(self, password_reset_token: str, new_password: Password) -> bool:
        """
        Reset the password of an account using a password reset token.

        Args:
            password_reset_token (str): The password reset token.
            new_password (Password): The new password to set for the account.

        Returns:
            bool: True if the password was successfully reset, False otherwise.
        """

        try:
            account = await self.get_account_by(password_reset_token=password_reset_token)

            if not account:
                raise errors.AccountNotFoundError()

            if not account.password_reset_token_created_at:
                raise errors.InvalidPasswordResetTokenError()

            if datetime.now(UTC) > (
                account.password_reset_token_created_at + timedelta(hours=settings.MAX_PASSWORD_RESET_TIME)
            ):
                raise errors.InvalidPasswordResetTokenError()

            hashed_password, salt = security_service.hash_password(password=new_password)

            await self.account_repository.update(
                account.id,
                {
                    "encrypted_password": hashed_password,
                    "password_salt": salt,
                    "last_password_change_at": datetime.now(UTC),
                    "password_reset_token": None,
                    "password_reset_token_created_at": None,
                },
            )

            return True
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.account_service.reset_account_password:: error while resetting password: {e}",
            )
            raise errors.AccountUpdateError(detail="Failed to reset account password", context="account_service") from e
        except errors.ServiceError as se:
            logger.exception(
                f"src.domain.services.account_service.reset_account_password:: error while resetting password: {se}",
            )
            raise se

    async def record_tracking_activity(
        self, *, account_id: IDType, ip_address: str | None, user_agent: str | None
    ) -> None:
        """
        Record meta activity for an account.

        Args:
            account_id (IDType): The ID of the account.
            ip_address (str | None): The IP address of the login activity.
            user_agent (str | None): The user agent of the login activity.

        Returns:
            None
        """

        try:
            account = await self.get_account_by(id=account_id)
            if not account:
                raise errors.AccountNotFoundError()

            account.last_sign_in_at = account.current_sign_in_at
            account.last_sign_in_ip = account.current_sign_in_ip
            account.last_sign_in_user_agent = user_agent
            account.current_sign_in_ip = ip_address
            account.sign_in_count += 1

            await self.account_repository.update(account.id, account)
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.account_service.record_tracking_activity:: error while recording tracking activity for account {account_id}: {e}",
            )
            raise errors.AccountUpdateError(
                detail="Failed to record login activity",
            ) from e
        except errors.ServiceError as se:
            logger.exception(
                f"src.domain.services.account_service.record_tracking_activity:: error while recording tracking activity for account {account_id}: {se}",
            )
            raise se

    async def verify_account(self, id: IDType) -> bool:
        """
        Mark an account as verified.

        Args:
            id (IDType): The ID of the account to verify.

        Returns:
            bool: True if the account was successfully verified, False otherwise.
        """

        try:
            account = await self.get_account_by(id=id)
            if not account:
                raise errors.AccountNotFoundError()

            await self.account_repository.update(
                account.id,
                AccountUpdate(
                    is_verified=True,
                    email_confirmed=True,
                    verified_at=datetime.now(UTC),
                ),
            )
            return True
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.account_service.verify_account:: error while verifying account {id}: {e}",
            )
            raise errors.AccountUpdateError(
                detail="Failed to verify account",
            ) from e
        except errors.ServiceError as se:
            logger.exception(
                f"src.domain.services.account_service.verify_account:: error while verifying account {id}: {se}",
            )
            raise se

    async def mark_account_for_deletion(self, id: IDType) -> bool:
        """
        Soft delete an account.

        Args:
            id (IDType): The ID of the account to delete.

        Returns:
            bool: True if the account was successfully soft deleted, False otherwise.
        """

        try:
            return await self.account_repository.soft_delete(id)
        except errors.DatabaseError as e:
            logger.exception(
                f"src.domain.services.account_service.delete_account:: error while deleting account {id}: {e}",
            )
            raise errors.AccountUpdateError(
                detail="Failed to delete account",
            ) from e
        except errors.ServiceError as se:
            logger.exception(
                f"src.domain.services.account_service.delete_account:: error while deleting account {id}: {se}",
            )
            raise se
