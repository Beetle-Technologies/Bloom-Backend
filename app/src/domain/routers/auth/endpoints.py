from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import (
    auth_rate_limit,
    is_bloom_client,
    is_bloom_user_client,
    is_not_bloom_user_client,
    per_minute_rate_limit,
    requires_eligible_account,
    strict_rate_limit,
)
from src.core.exceptions import errors
from src.core.helpers.request import get_request_info
from src.core.helpers.response import IResponseBase, build_json_response
from src.core.logging import get_logger
from src.core.types import BloomClientInfo, Password
from src.domain.schemas import (
    AuthForgotPasswordRequest,
    AuthLogoutRequest,
    AuthPasswordChangeRequest,
    AuthPasswordResetRequest,
    AuthPreCheckRequest,
    AuthPreCheckResponse,
    AuthRegisterRequest,
    AuthRegisterResponse,
    AuthSessionResponse,
    AuthSessionState,
    AuthTokenRefreshRequest,
    AuthTokenVerificationRequest,
    AuthUserSessionRequest,
    AuthUserSessionResponse,
    AuthVerificationRequest,
)
from src.domain.services import AuthService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/pre_check",
    dependencies=[strict_rate_limit],
    response_model=IResponseBase[AuthPreCheckResponse],
    status_code=status.HTTP_200_OK,
)
async def pre_check(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[AuthPreCheckRequest, Body(..., description="Pre check request body")],
) -> IResponseBase[AuthPreCheckResponse]:
    """
    Pre check account to validate if registeration or authentication is possible
    """
    try:
        auth_service = AuthService(session=session)

        data = await auth_service.pre_check(
            type_check=body.type,
            value=body.value,
            mode=body.mode,
        )

        return build_json_response(
            data=data,
            message="Pre-check completed successfully",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during pre-check: {e}")
        raise errors.ServiceError(
            detail="Failed to perform pre-check",
        ) from e


@router.post(
    "/request_email_verification",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[None],
    status_code=status.HTTP_200_OK,
)
async def request_email_verification(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[
        AuthVerificationRequest,
        Body(..., description="Email verification request body"),
    ],
) -> IResponseBase[None]:
    """
    Request email verification link or OTP
    """
    try:
        auth_service = AuthService(session=session)

        await auth_service.request_email_verification(
            client_type=request_client.app,
            fid=body.fid,
            mode=body.mode,
        )

        return build_json_response(
            data=None,
            message=f"If your account is registered and not verified, { 'a verification link' if body.mode.value == "state_key" else 'an OTP' } has been sent to your email.",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during email verification request: {e}")
        raise errors.ServiceError(
            detail="Failed to request email verification",
        ) from e


@router.post(
    "/verify_email",
    dependencies=[per_minute_rate_limit],
    response_model=IResponseBase[None],
    status_code=status.HTTP_200_OK,
)
async def verify_email(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[
        AuthTokenVerificationRequest,
        Body(..., description="Email token verification request body"),
    ],
) -> IResponseBase[None]:
    """
    Verify user email address
    """
    try:
        auth_service = AuthService(session=session)

        await auth_service.verify_email(
            token=body.token,
            mode=body.mode,
        )

        return build_json_response(
            data=None,
            message="Email verification successful",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during email verification: {e}")
        raise errors.ServiceError(
            detail="Failed to verify email",
        ) from e


@router.post(
    "/register",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[AuthRegisterResponse],
    status_code=status.HTTP_200_OK,
)
async def register(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_not_bloom_user_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[AuthRegisterRequest, Body(..., description="User registration request body")],
) -> IResponseBase[AuthRegisterResponse]:
    """
    Register a new account
    """

    try:
        auth_service = AuthService(session=session)
        request_info = get_request_info(request, keys=["ip_address", "user_agent"])

        data = await auth_service.register(
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            password=body.password,
            phone_number=body.phone_number,
            client_type=request_client.app,
            type_attributes=body.type_attributes,
            ip_address=request_info["ip_address"],
            user_agent=request_info["user_agent"],
        )

        return build_json_response(
            data=data,
            message="Registration successful",
        )  # type: ignore
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during registration: {e}")
        raise errors.ServiceError(detail="Failed to register account") from e


@router.post(
    "/login",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[AuthSessionResponse],
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> IResponseBase[AuthSessionResponse]:
    """
    Login user via Oauth2 password flow
    """

    try:
        auth_service = AuthService(session=session)
        request_info = get_request_info(request, keys=["ip_address", "user_agent"])

        data = await auth_service.login(
            email=body.username,
            password=Password(body.password),
            client_type=request_client.app,
            ip_address=request_info["ip_address"],
            user_agent=request_info["user_agent"],
        )

        return build_json_response(
            data=data,
            message="Login successful",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during login: {e}")
        raise errors.ServiceError(detail="Failed to login") from e


@router.post(
    "/request_new_session",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[AuthUserSessionResponse | None],
    status_code=status.HTTP_200_OK,
)
async def request_session(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_user_client],  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[AuthUserSessionRequest, Body(..., description="Request session request body")],
) -> IResponseBase[AuthUserSessionResponse | None]:
    """
    Request a new authenticated user session
    """
    try:
        auth_service = AuthService(session=session)
        request_info = get_request_info(request, keys=["ip_address", "user_agent"])

        data = await auth_service.request_new_session(
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            password=body.password,
            otp=body.otp,
            ip_address=request_info["ip_address"],
            user_agent=request_info["user_agent"],
            mode=body.mode,
        )

        if data is None:
            message = "An OTP has been sent if the email is registered."

            if body.mode == "register":
                message = "Account registered successfully"

            return build_json_response(data=None, message=message)

        return build_json_response(
            data=data,
            message="Session request successful",
        )  # type: ignore
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during session request: {e}")
        raise errors.ServiceError(
            detail="Failed to request new session",
        ) from e


@router.post(
    "/logout",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[None],
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],  # noqa: ARG001
    body: Annotated[AuthLogoutRequest, Body(..., description="Logout request body")],
) -> IResponseBase[None]:
    """
    Logout from current session and revoke tokens
    """
    try:
        auth_service = AuthService(session=session)

        await auth_service.logout(
            access_token=body.access_token,
            refresh_token=body.refresh_token,
        )

        return build_json_response(
            data=None,
            message="Logout successful",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during logout: {e}")
        raise errors.ServiceError(
            detail="Failed to logout",
        ) from e


@router.post(
    "/refresh",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[AuthSessionResponse],
    status_code=status.HTTP_200_OK,
)
async def refresh(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[AuthTokenRefreshRequest, Body(..., description="Token refresh request body")],
) -> IResponseBase[AuthSessionResponse]:
    """
    Refresh access token using access and refresh token
    """
    try:
        auth_service = AuthService(session=session)

        data = await auth_service.refresh_tokens(
            access_token=body.access_token,
            refresh_token=body.refresh_token,
        )

        return build_json_response(
            data=data,
            message="Token refresh successful",
        )  # type: ignore
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during token refresh: {e}")
        raise errors.ServiceError(
            detail="Failed to refresh tokens",
        ) from e


@router.post(
    "/request_forgot_password",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[None],
    status_code=status.HTTP_200_OK,
)
async def forgot_password(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[AuthForgotPasswordRequest, Body(..., description="Forgot password request body")],
) -> IResponseBase[None]:
    """
    Request password reset
    """
    try:
        auth_service = AuthService(session=session)

        await auth_service.request_password_reset(client_type=request_client.app, email=body.email)

        return build_json_response(
            data=None,
            message="If the email is registered, a password reset link has been sent",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during password reset request: {e}")
        raise errors.ServiceError(
            detail="Failed to request password reset",
        ) from e


@router.post(
    "/verify_password_reset",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[None],
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    request: Request,  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[AuthPasswordResetRequest, Body(..., description="Password reset request body")],
) -> IResponseBase[None]:
    """
    Reset user password using reset token
    """
    try:
        auth_service = AuthService(session=session)

        await auth_service.reset_password(
            token=body.token,
            new_password=body.new_password,
        )

        return build_json_response(
            data=None,
            message="Password reset successful",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during password reset: {e}")
        raise errors.ServiceError(
            detail="Failed to reset password",
        ) from e


@router.put(
    "/request_password_change",
    dependencies=[auth_rate_limit],
    response_model=IResponseBase[None],
    status_code=status.HTTP_200_OK,
)
async def change_password(
    request: Request,  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
    body: Annotated[AuthPasswordChangeRequest, Body(..., description="Password change request body")],
) -> IResponseBase[None]:
    """
    Change current user password
    """
    try:
        auth_service = AuthService(session=session)

        await auth_service.change_password(
            account_id=auth_state.id,
            current_password=body.current_password,
            new_password=body.new_password,
        )

        return build_json_response(
            data=None,
            message="Password changed successfully",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.error(f"Error occurred during password change: {e}")
        raise errors.ServiceError(
            detail="Failed to change password",
        ) from e
