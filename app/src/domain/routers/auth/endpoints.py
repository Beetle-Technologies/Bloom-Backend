from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import (
    auth_rate_limit,
    is_bloom_client,
    per_minute_rate_limit,
    requires_authenticated_account,
    strict_rate_limit,
)
from src.core.helpers.request import get_request_info
from src.core.helpers.response import IResponseBase, build_json_response
from src.core.types import BloomClientInfo, Password
from src.domain.schemas import AuthPreCheckRequest, AuthSessionResponse, AuthSessionState
from src.domain.services import AuthService

router = APIRouter()


@router.get("/pre_check", dependencies=[strict_rate_limit])
async def pre_check(
    request: Request,
    body: Annotated[AuthPreCheckRequest, Body(..., description="Pre check request body")],
):
    """
    Pre check account to validate if registeration or authentication is possible
    """
    pass


@router.post("/verify_email", dependencies=[per_minute_rate_limit])
async def verify_email(
    request: Request,
    body: Annotated[dict[str, str], Body(..., description="Email verification request body")],
):
    """
    Verify user email address
    """
    pass


@router.post("/register", dependencies=[auth_rate_limit])
async def register():
    """
    Register a new user account
    """
    pass


@router.post("/login", dependencies=[auth_rate_limit], response_model=IResponseBase[AuthSessionResponse])
async def login(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> IResponseBase[AuthSessionResponse]:
    """
    Login user via Oauth2 password flow
    """

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


@router.post("/logout", dependencies=[auth_rate_limit])
async def logout(
    request: Request,
    token_data: Annotated[AuthSessionState, Depends(requires_authenticated_account)],
):
    """
    Logout user and invalidate auth tokens
    """
    pass


@router.post("/refresh", dependencies=[auth_rate_limit])
async def refresh():
    """
    Refresh access token using refresh token
    """
    pass


@router.post("/forgot_password", dependencies=[auth_rate_limit])
async def forgot_password():
    """
    Request password reset
    """
    pass


@router.post("/reset_password", dependencies=[auth_rate_limit])
async def reset_password():
    """
    Reset user password using reset token
    """
    pass


@router.put("/change_password", dependencies=[auth_rate_limit])
async def change_password():
    """
    Change current user password
    """
    pass
