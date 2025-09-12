import time
from functools import lru_cache
from types import CoroutineType
from typing import Annotated, Any, Callable

from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from multidict import CIMultiDict
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.database.session import get_db_session
from src.core.exceptions import errors
from src.core.helpers.request import get_client_ip, parse_bloom_client_header
from src.core.types import BloomClientInfo
from src.domain.schemas import AuthSessionState
from src.domain.services import AccountService, TokenService, security_service
from src.libs.throttler import limiter


@lru_cache(maxsize=1)
def get_security_schemes() -> tuple[HTTPBearer, OAuth2PasswordBearer]:
    return (
        HTTPBearer(),
        OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_str}/auth/login"),
    )


def create_rate_limit_dependency(
    namespace: str,
    custom_limit: str | None = None,
    key_func: Callable[[Request], str] | None = None,
) -> Callable[..., CoroutineType[Any, Any, None]]:
    """
    Create a rate limit dependency for specific routes or routers.

    Args:
        namespace (str): The namespace for rate limiting (e.g., "auth", "api", "uploads")
        custom_limit (str | None): Optional custom limit string (e.g., "10/minute", "100/hour")
        key_func (Callable[[Request], str] | None): Optional function to extract client key from request

    Returns:
        Dependency function that can be used with FastAPI routes
    """

    def _default_key_func(request: Request) -> str:
        """Default function to generate client key from request"""
        client_ip = get_client_ip(request)
        return client_ip or "unknown"

    async def rate_limit_dependency(request: Request) -> None:
        """Rate limit dependency function"""
        client_key_func = key_func or _default_key_func
        client_key = client_key_func(request)

        allowed = await limiter.hit(
            namespace=namespace,
            client_key=client_key,
            custom_limit=custom_limit,
        )

        if not allowed:
            stats, limit_amount = await limiter.get_window_stats_with_limit(
                namespace=namespace,
                client_key=client_key,
                custom_limit=custom_limit,
            )

            current_time = time.time()
            retry_after = max(1, int(stats.reset_time - current_time))

            raise errors.RateLimitExceededError(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers=CIMultiDict(
                    {
                        "X-RateLimit-Limit": str(limit_amount),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(stats.reset_time)),
                        "Retry-After": str(retry_after),
                    }
                ),
            )

    return rate_limit_dependency


def validate_bloom_client_header(
    x_bloom_client: str = Header(None, alias="X-Bloom-Client", example="bloom_client")
) -> BloomClientInfo:
    """
    Validate and parse the X-Bloom-Client header.
    For OpenAPI docs endpoints, provides a default header value.

    Args:
        x_bloom_client (str): The X-Bloom-Client header value

    Returns:
        BloomClientInfo: Parsed client information
    """
    if not x_bloom_client:
        raise errors.InvalidClienTypeError(detail="X-Bloom-Client header is required")

    return parse_bloom_client_header(x_bloom_client)


auth_rate_limit = Depends(create_rate_limit_dependency("bloom_auth", "10/minute"))
api_rate_limit = Depends(create_rate_limit_dependency("bloom_api", "80/minute"))
upload_rate_limit = Depends(create_rate_limit_dependency("bloom_uploads", "5/minute"))
strict_rate_limit = Depends(create_rate_limit_dependency("bloom_strict", "5/minute"))
per_minute_rate_limit = Depends(create_rate_limit_dependency("bloom_per_minute", "1/minute"))
is_bloom_client = Depends(validate_bloom_client_header)


async def requires_authenticated_account(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_security_schemes()[0])],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthSessionState:
    """
    Dependency to ensure the request has a valid authenticated account via OAuth2 token.

    Args:
        credentials: The HTTP Authorization credentials
        session: Database session

    Returns:
        AuthSessionState: The validated token data

    Raises:
        AuthenticationError: If the token is invalid, missing, or revoked
    """
    if not credentials or not credentials.credentials:
        raise errors.InvalidTokenError()

    token = credentials.credentials

    decoded_token = security_service.decode_jwt_token(token)
    auth_data = security_service.get_token_data(decoded_token, AuthSessionState)

    token_service = TokenService(session=session)
    is_valid = await token_service.is_token_valid(token=token)

    if not is_valid:
        raise errors.InvalidTokenError()

    return auth_data


async def requires_eligible_account(
    auth_state: Annotated[AuthSessionState, Depends(requires_authenticated_account)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthSessionState:
    """
    Dependency to ensure the authenticated account is verified.

    Args:
        auth_state (AuthSessionState): The authenticated session state
        session (AsyncSession): The database session

    Returns:
        AuthSessionState: The authenticated and verified session state
    """

    account_service = AccountService(session=session)
    account = await account_service.get_account_by(id=auth_state.id)

    if not account:
        raise errors.AccountNotFoundError()

    if not account.is_eligible():
        raise errors.AccountIneligibleError(
            meta={
                "is_verified": account.is_verified,
                "is_active": account.is_active,
                "is_suspended": account.is_suspended,
                "is_locked": account.is_locked(),
            }
        )

    return auth_state


def require_eligible_user_account(
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
) -> AuthSessionState:
    """
    Dependency to ensure the authenticated account is a verified user account.

    Args:
        auth_state (AuthSessionState): The authenticated session state

    Returns:
        AuthSessionState: The verified user account session state
    """
    if not auth_state.type.is_user():
        raise errors.AccountIneligibleError(
            detail="Account is not a user account",
            meta={"account_type": auth_state.type.value},
        )

    return auth_state


def require_eligible_business_account(
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
) -> AuthSessionState:
    """
    Dependency to ensure the authenticated account is a verified business account.

    Args:
        auth_state (AuthSessionState): The authenticated session state

    Returns:
        AuthSessionState: The verified business account session state
    """

    if not auth_state.type.is_business():
        raise errors.AccountIneligibleError(
            detail="Account is not a business account",
            meta={"account_type": auth_state.type.value},
        )

    return auth_state


def require_eligible_supplier_account(
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
) -> AuthSessionState:
    """
    Dependency to ensure the authenticated account is a verified supplier account.

    Args:
        auth_state (AuthSessionState): The authenticated session

    Returns:
        AuthSessionState: The verified supplier account session state
    """

    if not auth_state.type.is_supplier():
        raise errors.AccountIneligibleError(
            detail="Account is not a supplier account",
            meta={"account_type": auth_state.type.value},
        )

    return auth_state


def require_eligible_admin_account(
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
) -> AuthSessionState:
    """
    Dependency to ensure the authenticated account is a verified admin account.

    Args:
        auth_state (AuthSessionState): The authenticated session

    Returns:
        AuthSessionState: The verified admin account session state
    """

    if not auth_state.type.is_admin():
        raise errors.AccountIneligibleError(
            detail="Account is not an admin account",
            meta={"account_type": auth_state.type.value},
        )

    return auth_state
