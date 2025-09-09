from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import status
from pydantic import EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.exceptions import errors
from src.core.security import generate_random_token, hash_password
from src.core.types import IDType, Password
from src.domain.models import Account
from src.domain.repositories import AccountRepository

logger = logging.getLogger(__name__)


class AccountService:
    """Service class for account-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_repository = AccountRepository(session=self.session)

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

            if account.is_eligible_for_login():
                raise errors.UnauthorizedError(
                    message="Account is not eligible for login.",
                    detail="Your account is either suspended, locked, or inactive. Please contact support if you believe this is an error.",
                )

            if account.check_reenumeration_attempts():
                if account.locked_at and (
                    datetime.now(UTC) - account.locked_at
                ) < timedelta(seconds=settings.MAX_LOGIN_RETRY_TIME):
                    raise errors.AccountLockedError()
                else:
                    account.locked_at = None
                    account.failed_attempts = 0

            if not account.check_password(password):
                account.failed_attempts += 1

                if account.failed_attempts >= settings.MAX_LOGIN_FAILED_ATTEMPTS:
                    account.locked_at = datetime.now(UTC)
                    account.unlock_token = generate_random_token()

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

    async def update_password(
        self, id: IDType, current_password: Password, new_password: Password
    ) -> Account:
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

            hashed_password, salt = hash_password(new_password)

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
                message="Failed to update password for account",
            ) from de
        except errors.ServiceError as se:
            raise se
