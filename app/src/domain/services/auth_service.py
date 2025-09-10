import logging

from pydantic import EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.enums import ClientType
from src.core.exceptions import errors
from src.core.types import Password
from src.domain.services.account_service import AccountService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_service = AccountService(session=self.session)

    async def login(
        self,
        *,
        email: EmailStr,
        password: Password,
        client_type: ClientType,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        """
        Authenticates a user and creates an authentication session.

        Args:
            email (EmailStr): The email of the user.
            password (Password): The password of the user.
            ip_address (str | None): The IP address of the user (optional).
            user_agent (str | None): The user agent string of the user's device (optional).

        Returns:
            AuthSessionResponse: The authentication session details.

        Raises:
            AuthenticationError: If authentication fails.
            AccountUpdateError: If there is an error updating the account.
            ServiceError: If there is an error during the authentication process.
        """

        try:
            account = await self.account_service.authenticate(
                email=email,
                password=password,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return account
        except errors.AuthenticationError as ae:
            logger.warning(f"AuthenticationError during login for email {email}: {ae.detail}")
            raise errors.AuthenticationError(
                detail="Invalid email or password. Please check your credentials.",
                status=ae.status,
            ) from ae
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.auth_service.login:: ServiceError during login for email {email}: {se.detail}",
                exc_info=True,
            )
            raise errors.AuthenticationError(
                detail=se.detail,
                status=se.status,
            ) from se
