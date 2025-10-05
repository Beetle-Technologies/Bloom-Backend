from datetime import UTC, datetime, timedelta
from typing import ClassVar, Literal

from pydantic import EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.database.decorators import transactional
from src.core.enums import ClientType
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import Password, PhoneNumber
from src.domain.enums import AccountTypeEnum, AuthPreCheckTypeEnum, TokenVerificationRequestTypeEnum
from src.domain.schemas import (
    AuthPreCheckResponse,
    AuthRegisterResponse,
    AuthSessionResponse,
    AuthSessionState,
    AuthUserSessionResponse,
    CachedAccountData,
    TokenCreate,
)
from src.domain.services.account_service import AccountService
from src.domain.services.account_type_info_service import AccountTypeInfoService
from src.domain.services.permission_service import PermissionService
from src.domain.services.request_service import request_service
from src.domain.services.security_service import security_service
from src.domain.services.token_service import TokenService
from src.domain.tasks.mailer import send_email_task
from src.libs.cache import get_cache_service
from src.libs.mailer import MailerRequest

logger = get_logger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_service = AccountService(session=self.session)
        self.account_type_info_service = AccountTypeInfoService(session=self.session)
        self.permission_service = PermissionService(session=self.session)
        self.token_service = TokenService(session=self.session)
        self.security_service = security_service
        self.cache_service = get_cache_service()
        self.request_service = request_service

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
    ) -> AuthRegisterResponse:
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
                    metadata={"client_type": client_type.value},
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

            # If account is already verified during registration, cache it
            if account.is_verified:
                await self._cache_verified_account(account)

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
            raise errors.AccountCreationError(detail=se.detail, metadata=getattr(se, "metadata", None)) from se
        except AssertionError as ae:
            logger.error(
                f"src.domain.services.auth_service.register:: AssertionError during registration for email {email}: {str(ae)}",
                exc_info=True,
            )
            raise errors.AccountCreationError(
                detail="Registration failed due to an unexpected error",
            ) from ae
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.register:: Unexpected error during registration for email {email}: {str(e)}",
                exc_info=True,
            )
            raise errors.AccountCreationError(
                detail="Registration failed due to an unexpected error",
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

            # Check for suspicious login (IP address change) and send notification
            if ip_address and account.last_sign_in_ip:
                await self._send_suspicious_login_notification(
                    account=account,
                    client_type=client_type,
                    current_ip_address=ip_address,
                    previous_ip_address=account.last_sign_in_ip,
                    user_agent=user_agent,
                    login_time=datetime.now(UTC),
                )

            expected_account_type = self.CLIENT_TYPE_TO_ACCOUNT_TYPE_MAPPING.get(client_type)

            if not expected_account_type:
                raise errors.AuthenticationError(
                    detail="Unsupported authentication client for this account",
                    metadata={"client_type": client_type.value},
                )

            account_type_info = account.get_account_type_infos(account_type=expected_account_type)

            if not account_type_info:
                raise errors.AuthenticationError(
                    detail="Account does not have the required type for this client",
                    metadata={
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

            await self.token_service.bulk_create_if_not_exists(
                tokens=[
                    TokenCreate(
                        token=auth_token.token,
                        deleted_datetime=datetime.now(UTC) + timedelta(seconds=auth_token.expires_in),
                    )
                    for auth_token in auth_tokens
                ]
            )

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
            raise se
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.login:: Unexpected error during login for email {email}: {str(e)}",
                exc_info=True,
            )
            raise errors.AuthenticationError(
                detail="Login failed due to an unexpected error",
            ) from e

    async def send_code_for_session(
        self,
        *,
        client_type: ClientType,
        fid: str,
    ) -> None:
        """
        Request an email verification to be sent to the specified email address.

        Args:
            email (EmailStr): The email address to send the verification to.

        Raises:
            ServiceError: If there is an error during the process.
        """
        try:
            account = await self.account_service.get_account_by(friendly_id=fid)
            if not account:
                return

            token = self.security_service.generate_totp()

            await self.account_service.update_account(
                id=account.id,
                account_update={
                    "confirmation_token": token,
                    "confirmation_token_sent_at": datetime.now(UTC),
                },
            )

            send_email_task.delay(
                payload=MailerRequest(
                    subject="Request a new session",
                    sender=settings.MAILER_DEFAULT_SENDER,
                    recipients=[account.email],
                    template_name="v1/auth/request_new_session.mjml.html",
                    template_context={
                        "first_name": account.first_name,
                        "email": account.email,
                        "token": token,
                        "validity_time": (settings.AUTH_OTP_MAX_AGE // 60),
                        "client_type": client_type.value,
                    },
                ).model_dump()
            )
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.auth_service.send_code_for_session:: ServiceError: {se.detail}",
                exc_info=True,
            )
            raise se
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.send_code_for_session:: Unexpected error: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Failed to send session OTP",
            ) from e

    async def verify_code_for_session(
        self,
        *,
        token: str,
    ) -> None:
        """
        Verify the email address using the provided token.

        Args:
            token (str): The verification token received by the user.

        Raises:
            VerificationError: If the token is invalid or verification fails.
            ServiceError: If there is an error during the process.
        """

        try:
            otp = self.security_service.verify_totp(token=token)

            if not otp:
                raise errors.InvalidOTPError()

            account = await self.account_service.get_account_by(confirmation_token=token)
            if not account:
                raise errors.AccountNotFoundError()

            if (
                not account.confirmation_token_sent_at
                or (datetime.now(UTC) - account.confirmation_token_sent_at).total_seconds() > settings.AUTH_OTP_MAX_AGE
            ):
                raise errors.InvalidOTPError()

            if not account.is_verified:
                updated_account = await self.account_service.update_account(
                    id=account.id,
                    account_update={
                        "is_verified": True,
                        "confirmation_token": None,
                        "confirmation_token_sent_at": None,
                        "email_confirmed": True,
                        "is_active": True,
                        "confirmed_at": datetime.now(UTC),
                    },
                )

                if updated_account:
                    await self._cache_verified_account(updated_account)

        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.auth_service.verify_code_for_session:: ServiceError: {se.detail}",
                exc_info=True,
            )
            raise se
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.verify_code_for_session:: Unexpected error: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Failed to verify session OTP",
            ) from e

    async def request_email_verification(
        self,
        *,
        client_type: ClientType,
        fid: str,
        mode: TokenVerificationRequestTypeEnum,
    ) -> None:
        """
        Request an email verification to be sent to the specified email address.

        Args:
            email (EmailStr): The email address to send the verification to.

        Raises:
            ServiceError: If there is an error during the process.
        """
        try:
            account = await self.account_service.get_account_by(friendly_id=fid)
            if not account:
                return

            if account.is_verified:
                return

            token: str | None = None

            if mode == TokenVerificationRequestTypeEnum.OTP:
                token = self.security_service.generate_totp()
            else:
                token = self.security_service.generate_email_verification_token(fid=fid)

            assert token is not None, "Token generation failed"

            await self.account_service.update_account(
                id=account.id,
                account_update={
                    "confirmation_token": token,
                    "confirmation_token_sent_at": datetime.now(UTC),
                },
            )

            send_email_task.delay(
                payload=MailerRequest(
                    subject="Verify Your Email Address",
                    sender=settings.MAILER_DEFAULT_SENDER,
                    recipients=[account.email],
                    template_name="v1/auth/email_verification.mjml.html",
                    template_context={
                        "first_name": account.first_name,
                        "email": account.email,
                        "token": token,
                        "mode": mode.value,
                        "validity_time": (
                            (settings.AUTH_VERIFICATION_TOKEN_MAX_AGE // 3600)
                            if mode == TokenVerificationRequestTypeEnum.STATE_KEY
                            else (settings.AUTH_OTP_MAX_AGE // 60)
                        ),
                        "client_type": client_type.value,
                    },
                ).model_dump()
            )
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.auth_service.request_email_verification:: ServiceError: {se.detail}",
                exc_info=True,
            )
            raise se
        except AssertionError as ae:
            logger.error(
                f"src.domain.services.auth_service.request_email_verification:: AssertionError: {str(ae)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Failed to generate verification token",
            ) from ae
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.request_email_verification:: Unexpected error: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Failed to request email verification",
            ) from e

    async def verify_email(
        self,
        *,
        token: str,
        mode: TokenVerificationRequestTypeEnum,
        is_reset: bool,
    ) -> None:
        """
        Verify the email address using the provided token.

        Args:
            token (str): The verification token received by the user.
            mode (TokenVerificationRequestTypeEnum): The mode of verification (OTP or STATE_KEY).

        Raises:
            VerificationError: If the token is invalid or verification fails.
            ServiceError: If there is an error during the process.
        """

        try:
            if mode == TokenVerificationRequestTypeEnum.STATE_KEY:
                fid = self.security_service.verify_email_verification_token(token=token)

                account = await self.account_service.get_account_by(friendly_id=fid)
                if not account:
                    raise errors.AccountNotFoundError()

                if account.is_verified:
                    return
                if account.confirmation_token != token:
                    raise errors.InvalidVerificationLinkError()
            else:
                otp = self.security_service.verify_totp(token=token)

                if not otp:
                    raise errors.InvalidOTPError()

                account = await self.account_service.get_account_by(confirmation_token=token)

                if not account:
                    raise errors.AccountNotFoundError()

                if account.is_verified:
                    return
                if (
                    not account.confirmation_token_sent_at
                    or (datetime.now(UTC) - account.confirmation_token_sent_at).total_seconds()
                    > settings.AUTH_OTP_MAX_AGE
                ):
                    raise errors.InvalidOTPError()

            if not is_reset:
                await self.account_service.update_account(
                    id=account.id,
                    account_update={
                        "is_verified": True,
                        "confirmation_token": None,
                        "confirmation_token_sent_at": None,
                        "email_confirmed": True,
                        "is_active": True,
                        "confirmed_at": datetime.now(UTC),
                    },
                )

                await self._cache_verified_account(account)
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.auth_service.verify_email:: ServiceError: {se.detail}",
                exc_info=True,
            )
            raise se
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.verify_email:: Unexpected error: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Failed to verify email",
            ) from e

    async def logout(
        self,
        *,
        access_token: str,
        refresh_token: str | None,
    ) -> None:
        """
        Logout a user by revoking their access and refresh tokens.

        Args:
            access_token (str): The access token to revoke
            refresh_token (str): The refresh token to revoke

        Raises:
            ServiceError: If there is an error during the logout process
        """
        try:
            access_revoked = await self.token_service.revoke_token(token=access_token)

            if not access_revoked:
                logger.warning("src.domain.services.auth_service.logout:: Access token was not revoked during logout")

            if refresh_token:
                refresh_revoked = await self.token_service.revoke_token(token=refresh_token)

                if not refresh_revoked:
                    logger.warning(
                        "src.domain.services.auth_service.logout:: Refresh token was not revoked during logout"
                    )

        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.logout:: Unexpected error during logout: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Logout failed due to an unexpected error",
            ) from e

    async def pre_check(
        self,
        *,
        type_check: AuthPreCheckTypeEnum,
        value: str,
        mode: Literal["register", "login"],
    ) -> AuthPreCheckResponse:
        """
        Pre-check if an email or username exists for registration or login purposes.

        Args:
            type_check (AuthPreCheckTypeEnum): The type of check to perform ("email" or "username")
            value (str): The email or username value to check
            mode (Literal["register", "login"]): The mode of operation ("register" or "login")

        Returns:
            AuthPreCheckResponse: the data containing pre-check results
        """
        try:
            if mode == "register":
                cache_key = f"accounts:verified:{type_check}:{value}"
                cached_data = await self.cache_service.get(cache_key)

                if cached_data:
                    return AuthPreCheckResponse(
                        exists=True, is_verified=True, can_login=True, gid=cached_data.id, fid=cached_data.fid
                    )

                kwargs = {f"{type_check.value}": value}
                account = await self.account_service.get_account_by(**kwargs)

                if account:
                    if account.is_verified:
                        await self._cache_verified_account(account)

                    return AuthPreCheckResponse(
                        exists=True,
                        is_verified=account.is_verified,
                        gid=account.id,
                        fid=account.friendly_id,
                        can_login=account.is_verified,
                    )

                return AuthPreCheckResponse(exists=False, is_verified=False, gid=None, fid=None, can_login=False)

            elif mode == "login":
                cache_key = f"accounts:verified:{type_check}:{value}"
                cached_data = await self.cache_service.get(cache_key)

                if cached_data:
                    return AuthPreCheckResponse(
                        exists=True, is_verified=True, can_login=True, gid=cached_data.id, fid=cached_data.fid
                    )

                kwargs = {f"{type_check.value}": value, "is_verified": True}
                account = await self.account_service.get_account_by(**kwargs)

                if account:
                    await self._cache_verified_account(account)

                    return AuthPreCheckResponse(
                        exists=True, is_verified=True, can_login=True, gid=account.id, fid=account.friendly_id
                    )

                kwargs = {f"{type_check.value}": value, "is_verified": True}
                account = await self.account_service.get_account_by(**kwargs)

                if account:
                    await self._cache_verified_account(account)

                    return AuthPreCheckResponse(
                        exists=True, is_verified=True, can_login=True, gid=account.id, fid=account.friendly_id
                    )

                kwargs = {f"{type_check.value}": value}
                account = await self.account_service.get_account_by(**kwargs)

                if account:
                    return AuthPreCheckResponse(
                        exists=True,
                        is_verified=False,
                        can_login=False,
                        gid=account.id,
                        fid=account.friendly_id,
                    )

                return AuthPreCheckResponse(exists=False, is_verified=False, can_login=False, gid=None, fid=None)

            else:
                raise ValueError(f"Invalid mode: {mode}")

        except (Exception, ValueError) as e:
            logger.error(
                f"src.domain.services.auth_service.pre_check:: Pre-check failed for {type_check}={value}, mode={mode}: {str(e)}"
            )
            raise errors.ServiceError(
                detail="Pre-check operation failed",
            ) from e

    @transactional
    async def request_new_session(
        self,
        *,
        first_name: str | None,
        last_name: str | None,
        email: EmailStr,
        password: Password | None,
        otp: str | None,
        mode: Literal["register", "trigger_login", "login"],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthUserSessionResponse | None:
        """
        Request a new authentication session by creating a new account and logging in.

        Args:
            first_name (str): The first name of the
            last_name (str): The last name of the user
            email (EmailStr): The email address of the user
            password (Password): The password for the account
            otp (str | None): The OTP for email verification (if required)
            mode (Literal["register", "trigger_login", "login"]): The mode of operation
            ip_address (str | None): The IP address of the user (optional)
            user_agent (str | None): The user agent string (optional)

        Returns:
            AuthSessionResponse: The authentication session details with access and refresh tokens.

        Raises:
            ServiceError: If there is an error during the process.
        """
        try:

            if first_name and last_name and email and password and mode == "register":
                existing_account = await self.account_service.get_account_by(email=email)
                if existing_account:
                    raise errors.AccountCreationError(
                        detail="An account with this email already exists",
                    )

                account = await self.account_service.create_account(
                    first_name=first_name,
                    last_name=last_name,
                    username=None,
                    email=email,
                    password=password,
                    phone_number=None,
                )

                account_type_info = await self.account_type_info_service.create_account_type_info(
                    account_id=account.id,
                    account_type=AccountTypeEnum.USER,
                )

                await self.permission_service.assign_permissions_to_account_type_info(
                    account_type_info_id=account_type_info.id,
                    account_type=AccountTypeEnum.USER,
                    assigned_by=None,
                )

                await self.account_service.record_tracking_activity(
                    account_id=account.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

                assert account.friendly_id is not None

                return None
            elif email and mode == "trigger_login":
                account = await self.account_service.get_account_by(email=email)
                if not account:
                    raise errors.AuthenticationError(
                        detail="Account not found",
                    )

                await self.send_code_for_session(
                    client_type=ClientType.BLOOM_MAIN,
                    fid=account.friendly_id,  # type: ignore
                )

                return None
            elif email and otp and mode == "login":
                account = await self.account_service.get_account_by(email=email)
                if not account:
                    raise errors.AuthenticationError(
                        detail="Account not found",
                    )

                await self.verify_code_for_session(token=otp)

                account_type_info = account.get_account_type_infos(account_type=AccountTypeEnum.USER)
                if not account_type_info:
                    raise errors.AuthenticationError(
                        detail="Account not found",
                    )

                auth_session_state = AuthSessionState(
                    id=account.id,
                    type_info_id=account_type_info.id,
                    type=AccountTypeEnum.USER,
                )

                auth_tokens = self.security_service.generate_auth_tokens(auth_session_state)

                access_token = next((t for t in auth_tokens if t.scope == "access"), None)
                if not access_token:
                    raise errors.ServiceError(
                        detail="Failed to generate access token",
                    )

                await self.token_service.bulk_create_if_not_exists(
                    tokens=[
                        TokenCreate(
                            token=access_token.token,
                            deleted_datetime=datetime.now(UTC) + timedelta(seconds=access_token.expires_in),
                        )
                    ]
                )

                return AuthUserSessionResponse(token=access_token)
            else:
                raise errors.ServiceError(
                    detail="Invalid registration or OTP for login",
                )
        except errors.ServiceError as se:
            logger.error(
                f"src.domain.services.auth_service.request_new_session:: ServiceError during new session request for email {email}: {se.detail}",
                exc_info=True,
            )
            raise se
        except AssertionError as ae:
            logger.error(
                f"src.domain.services.auth_service.request_new_session:: AssertionError during new session request for email {email}: {str(ae)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Failed to create new session due to an unexpected error",
            ) from ae
        except Exception as e:
            logger.error(
                f"src.domain.services.auth_service.request_new_session:: Unexpected error during new session request for email {email}: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Failed to create new session due to an unexpected error",
            ) from e

    @transactional
    async def refresh_tokens(
        self,
        *,
        access_token: str,
        refresh_token: str,
    ) -> AuthSessionResponse:
        """
        Refresh authentication tokens using a valid refresh token.

        Args:
            access_token (str): The current access token (for validation)
            refresh_token (str): The refresh token to use for generating new tokens

        Returns:
            AuthSessionResponse: New authentication tokens

        Raises:
            ServiceError: If token refresh fails
        """
        try:
            decoded_refresh_token = self.security_service.decode_jwt_token(refresh_token)
            auth_data = self.security_service.get_token_data(decoded_refresh_token, AuthSessionState)

            is_refresh_valid = await self.token_service.is_token_valid(token=refresh_token)
            if not is_refresh_valid:
                raise errors.InvalidTokenError(detail="Refresh token is invalid or expired")

            account = await self.account_service.get_account_by(id=auth_data.id)
            if not account or not account.is_eligible():
                raise errors.AccountIneligibleError(detail="Account is not eligible for token refresh")

            await self.token_service.revoke_token(token=access_token)
            await self.token_service.revoke_token(token=refresh_token)

            new_auth_tokens = self.security_service.generate_auth_tokens(auth_data)

            await self.token_service.bulk_create_if_not_exists(
                tokens=[
                    TokenCreate(
                        token=auth_token.token,
                        deleted_datetime=datetime.now(UTC) + timedelta(seconds=auth_token.expires_in),
                    )
                    for auth_token in new_auth_tokens
                ]
            )

            return AuthSessionResponse(tokens=new_auth_tokens)
        except errors.InvalidTokenError as ite:
            logger.warning(f"Invalid token during refresh: {ite.detail}")
            raise ite
        except errors.ServiceError as se:
            logger.error(f"Service error during token refresh: {se.detail}", exc_info=True)
            raise se
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
            raise errors.ServiceError(
                detail="Token refresh failed",
            ) from e

    async def request_password_reset(
        self,
        *,
        client_type: ClientType,
        email: EmailStr,
    ) -> None:
        """
        Request a password reset for an account.

        Args:
            email (EmailStr): The email address of the account

        Raises:
            ServiceError: If the password reset request fails
        """
        try:
            account = await self.account_service.get_account_by(email=email)
            if not account:
                logger.debug(f"Password reset requested for non-existent email: {email}")
                return

            if client_type not in [ClientType.BLOOM_ADMIN]:
                token = self.security_service.generate_totp()

                await self.account_service.update_account(
                    id=account.id,
                    account_update={
                        "confirmation_token": token,
                        "confirmation_token_sent_at": datetime.now(UTC),
                    },
                )

                send_email_task.delay(
                    payload=MailerRequest(
                        subject="Password Reset Request",
                        sender=settings.MAILER_DEFAULT_SENDER,
                        recipients=[account.email],
                        template_name="v1/auth/password_reset.mjml.html",
                        template_context={
                            "first_name": account.first_name,
                            "email": account.email,
                            "token": token,
                            "mode": TokenVerificationRequestTypeEnum.OTP.value,
                            "validity_time": (settings.AUTH_OTP_MAX_AGE // 60),
                        },
                    ).model_dump()
                )
            else:
                token = await self.account_service.request_password_reset(email=email)

                send_email_task.delay(
                    payload=MailerRequest(
                        subject="Password Reset Request",
                        sender=settings.MAILER_DEFAULT_SENDER,
                        recipients=[account.email],
                        template_name="v1/auth/password_reset.mjml.html",
                        template_context={
                            "first_name": account.first_name,
                            "email": account.email,
                            "token": token,
                            "mode": TokenVerificationRequestTypeEnum.STATE_KEY.value,
                            "validity_time": (settings.MAX_PASSWORD_RESET_TIME // 3600),
                        },
                    ).model_dump()
                )

        except errors.ServiceError as se:
            logger.error(
                f"Service error during password reset request: {se.detail}",
                exc_info=True,
            )
            raise se
        except Exception as e:
            logger.error(
                f"Unexpected error during password reset request: {str(e)}",
                exc_info=True,
            )
            raise errors.ServiceError(
                detail="Failed to process password reset request",
            ) from e

    async def reset_password(
        self,
        *,
        token: str,
        fid: str | None,
        new_password: Password,
    ) -> None:
        """
        Reset account password using a password reset token.

        Args:
            token (str): The password reset token
            new_password (Password): The new password

        Raises:
            ServiceError: If password reset fails
        """
        try:

            if not fid:
                success = await self.account_service.reset_account_password(
                    password_reset_token=token,
                    new_password=new_password,
                )

                if not success:
                    raise errors.ServiceError(
                        detail="Password reset failed",
                    )

            if fid:
                account = await self.account_service.get_account_by(friendly_id=fid)
                if not account:
                    raise errors.AccountNotFoundError()

                encrypted_password, password_salt = self.security_service.hash_password(password=new_password)

                updated_account = await self.account_service.update_account(
                    id=account.id,
                    account_update={
                        "encrypted_password": encrypted_password,
                        "password_salt": password_salt,
                        "last_password_change_at": datetime.now(UTC),
                        "confirmation_token": None,
                        "confirmation_token_sent_at": None,
                    },
                )
                if not updated_account:
                    raise errors.ServiceError(
                        detail="Failed to update password",
                    )

                await self._invalidate_account_cache(account)

        except errors.InvalidPasswordResetTokenError as iprt:
            logger.warning(f"Invalid password reset token used: {iprt.detail}")
            raise iprt
        except errors.ServiceError as se:
            logger.error(f"Service error during password reset: {se.detail}", exc_info=True)
            raise se
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {str(e)}", exc_info=True)
            raise errors.ServiceError(
                detail="Failed to reset password",
            ) from e

    async def change_password(
        self,
        *,
        account_id: str,
        current_password: Password,
        new_password: Password,
    ) -> None:
        """
        Change password for an authenticated account.

        Args:
            account_id (str): The ID of the account
            current_password (Password): The current password
            new_password (Password): The new password

        Raises:
            ServiceError: If password change fails
        """
        try:
            updated_account = await self.account_service.update_password(
                id=account_id,
                current_password=current_password,
                new_password=new_password,
            )

            if not updated_account:
                raise errors.ServiceError(
                    detail="Failed to update password",
                )

        except errors.AccountInvalidPasswordError as aip:
            logger.warning(f"Invalid current password for account {account_id}")
            raise aip
        except errors.AccountChangePasswordMismatchError as acpm:
            logger.warning(f"New password same as current for account {account_id}")
            raise acpm
        except errors.ServiceError as se:
            logger.error(f"Service error during password change: {se.detail}", exc_info=True)
            raise se
        except Exception as e:
            logger.error(f"Unexpected error during password change: {str(e)}", exc_info=True)
            raise errors.ServiceError(
                detail="Failed to change password",
            ) from e

    async def _cache_verified_account(self, account) -> None:
        """
        Cache verified account data for pre-check functionality.

        Args:
            account: The verified account to cache
        """
        try:
            cached_data = CachedAccountData(
                id=account.id, friendly_id=account.friendly_id, email=account.email, username=account.username
            )

            email_key = f"accounts:verified:email:{account.email}"
            await self.cache_service.set(
                key=email_key,
                value=cached_data.model_dump(),
                ttl=3600 * 24 * 7,  # Cache for 7 days
            )

            # Cache by username if it exists
            if account.username:
                username_key = f"accounts:verified:username:{account.username}"
                await self.cache_service.set(
                    key=username_key,
                    value=cached_data.model_dump(),
                    ttl=3600 * 24 * 7,  # Cache for 7 days
                )

            logger.debug(f"Cached verified account data for email: {account.email}")

        except Exception as e:
            logger.error(f"Failed to cache verified account data: {str(e)}")

    async def _invalidate_account_cache(self, account) -> None:
        """
        Invalidate cached account data.

        Args:
            account: The account to invalidate cache for
        """
        try:
            email_key = f"accounts:verified:email:{account.email}"
            await self.cache_service.delete(email_key)

            if account.username:
                username_key = f"accounts:verified:username:{account.username}"
                await self.cache_service.delete(username_key)

            logger.debug(f"Invalidated cache for account: {account.email}")

        except Exception as e:
            logger.error(f"Failed to invalidate account cache: {str(e)}")

    async def _send_suspicious_login_notification(
        self,
        *,
        account,
        client_type: ClientType,
        current_ip_address: str | None,
        previous_ip_address: str | None,
        user_agent: str | None,
        login_time: datetime,
    ) -> None:
        """
        Send a suspicious login notification email when login is detected from a new IP address.

        Args:
            account: The account that was logged in to
            client_type (ClientType): The type of client making the request
            current_ip_address (str | None): The current IP address used for login
            previous_ip_address (str | None): The previous IP address on record
            user_agent (str | None): The user agent string
            login_time (datetime): The time of the login attempt
        """
        try:
            # Only send notification if we have both IP addresses and they're different
            if not current_ip_address or not previous_ip_address or current_ip_address == previous_ip_address:
                return

            template_context = {
                "first_name": account.first_name,
                "email": account.email,
                "client_type": client_type.value,
                "current_ip_address": current_ip_address,
                "previous_ip_address": previous_ip_address,
                "user_agent": user_agent,
                "login_time": login_time,
                "location": await self.request_service.get_location(current_ip_address),
            }

            mailer_request = MailerRequest(
                template_name="v1/auth/suspicious_login_notification.mjml.html",
                template_context=template_context,
                sender=settings.MAILER_DEFAULT_SENDER,
                recipients=[account.email],
                subject=f"Security Alert: New login to your {settings.APP_NAME} account",
            ).model_dump()

            send_email_task.delay(mailer_request)
        except Exception as e:
            logger.error(
                f"Failed to send suspicious login notification for account {account.id}: {str(e)}",
                exc_info=True,
            )
