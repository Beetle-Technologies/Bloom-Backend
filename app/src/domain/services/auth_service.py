import logging
from typing import ClassVar

from pydantic import EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.decorators import transactional
from src.core.enums import ClientType
from src.core.exceptions import errors
from src.core.types import Password, PhoneNumber
from src.domain.enums import AccountTypeEnum
from src.domain.schemas import AuthRegisterResponse, AuthSessionResponse, AuthSessionState
from src.domain.services.account_service import AccountService
from src.domain.services.account_type_info_service import AccountTypeInfoService
from src.domain.services.permission_service import PermissionService
from src.domain.services.security_service import security_service
from src.domain.services.token_service import TokenService
from src.libs.cache import get_cache_service

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_service = AccountService(session=self.session)
        self.account_type_info_service = AccountTypeInfoService(session=self.session)
        self.permission_service = PermissionService(session=self.session)
        self.token_service = TokenService(session=self.session)
        self.security_service = security_service
        self.cache_service = get_cache_service()

    CLIENT_TYPE_TO_ACCOUNT_TYPE_MAPPING: ClassVar[dict[ClientType, AccountTypeEnum]] = {
        ClientType.BLOOM_MAIN: AccountTypeEnum.USER,
        ClientType.BLOOM_ADMIN: AccountTypeEnum.ADMIN,
        ClientType.BLOOM_SUPPLIER: AccountTypeEnum.SUPPLIER,
        ClientType.BLOOM_BUSINESS: AccountTypeEnum.BUSINESS,
    }

    @transactional
    async def register(
        self,
        *,
        first_name: str,
        last_name: str,
        email: EmailStr,
        password: Password,
        phone_number: PhoneNumber | None = None,
        client_type: ClientType,
        type_attributes: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        """
        Register a new account with the specified client type and attributes.

        Args:
            first_name (str): The first name of the user
            last_name (str): The last name of the user
            email (EmailStr): The email address of the user
            password (Password): The password for the account
            phone_number (PhoneNumber | None): The phone number (optional)
            client_type (ClientType): The type of client making the request
            type_attributes (dict | None): Attributes specific to the account type
            ip_address (str | None): The IP address of the user (optional)
            user_agent (str | None): The user agent string (optional)

        Returns:
            Account: The created account

        Raises:
            AccountCreationError: If account creation fails
            ServiceError: If any other error occurs during registration
        """
        try:
            account = await self.account_service.create_account(
                first_name=first_name,
                last_name=last_name,
                username=None,
                email=email,
                password=password,
                phone_number=phone_number,
            )

            account_type = self.CLIENT_TYPE_TO_ACCOUNT_TYPE_MAPPING.get(client_type)
            if not account_type:
                raise errors.AuthenticationError(
                    detail="Unsupported authentication client for this account",
                    status=400,
                    meta={"client_type": client_type.value},
                )

            account_type_info = await self.account_type_info_service.create_account_type_info(
                account_id=account.id,
                account_type=account_type,
                attributes=type_attributes or {},
            )

            await self.permission_service.assign_permissions_to_account_type_info(
                account_type_info_id=account_type_info.id,
                account_type=account_type,
                assigned_by=None,
            )

            await self.account_service.record_tracking_activity(
                account_id=account.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            assert account.friendly_id is not None

            return AuthRegisterResponse(
                fid=account.friendly_id,
                is_verified=account.is_verified,
            )

        except errors.AccountCreationError as ace:
            logger.warning(
                f"src.domain.services.auth_service.register:: AccountCreationError during registration for email {email}: {ace.detail}"
            )
            raise ace
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.auth_service.register:: ServiceError during registration for email {email}: {se.detail}",
                exc_info=True,
            )
            raise errors.AccountCreationError(
                detail=se.detail, status=se.status, meta=getattr(se, "meta", None)
            ) from se
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.register:: Unexpected error during registration for email {email}: {str(e)}",
                exc_info=True,
            )
            raise errors.AccountCreationError(
                detail="Registration failed due to an unexpected error",
                status=500,
            ) from e

    async def login(
        self,
        *,
        email: EmailStr,
        password: Password,
        client_type: ClientType,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthSessionResponse:
        """
        Authenticates a user and creates an authentication session.

        Args:
            email (EmailStr): The email of the user.
            password (Password): The password of the user.
            client_type (ClientType): The type of client making the request.
            ip_address (str | None): The IP address of the user (optional).
            user_agent (str | None): The user agent string of the user's device (optional).

        Returns:
            AuthSessionResponse: The authentication session details with access and refresh tokens.

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

            expected_account_type = self.CLIENT_TYPE_TO_ACCOUNT_TYPE_MAPPING.get(client_type)

            if not expected_account_type:
                raise errors.AuthenticationError(
                    detail="Unsupported authentication client for this account",
                    status=400,
                    meta={"client_type": client_type.value},
                )

            account_type_info = account.get_account_type_infos(account_type=expected_account_type)

            if not account_type_info:
                raise errors.AuthenticationError(
                    detail="Account does not have the required type for this client",
                    status=403,
                    meta={
                        "client_type": client_type.value,
                        "required_account_type": expected_account_type.value,
                    },
                )

            auth_session_state = AuthSessionState(
                id=account.id,
                type_info_id=account_type_info.id,
                type=expected_account_type,
            )

            auth_tokens = self.security_service.generate_auth_tokens(auth_session_state)

            return AuthSessionResponse(tokens=auth_tokens)
        except errors.AuthenticationError as ae:
            logger.warning(
                f"src.domain.services.auth_service.login:: AuthenticationError during login for email {email}: {ae.detail}"
            )
            raise ae
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.auth_service.login:: ServiceError during login for email {email}: {se.detail}",
                exc_info=True,
            )
            raise errors.AuthenticationError(
                detail=se.detail,
                status=se.status,
            ) from se
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.login:: Unexpected error during login for email {email}: {str(e)}",
                exc_info=True,
            )
            raise errors.AuthenticationError(
                detail="Login failed due to an unexpected error",
                status=500,
            ) from e
