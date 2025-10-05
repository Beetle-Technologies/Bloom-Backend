import time
from functools import lru_cache
from types import CoroutineType
from typing import Annotated, Any, Callable

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from multidict import CIMultiDict
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.core.database.session import get_db_session
from src.core.exceptions import errors
from src.core.helpers.request import get_client_ip, parse_bloom_client_header
from src.core.types import BloomClientInfo
from src.domain.repositories import AccountTypeInfoRepository
from src.domain.schemas import AuthSessionState
from src.domain.services import AccountService, TokenService, security_service
from src.libs.storage import StorageService, storage_service
from src.libs.throttler import limiter


@lru_cache(maxsize=1)
def get_security_schemes() -> tuple[HTTPBearer, OAuth2PasswordBearer]:
    return (
        HTTPBearer(),
        OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_str}/auth/login"),
    )


def get_storage_service() -> StorageService:
    """
    Dependency to get the storage service instance.

    Returns:
        The storage service instance
    """
    return storage_service


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
    x_bloom_client: str = Header(
        None,
        alias="X-Bloom-Client",
        example="platform=web; version=1.0.0; app=bloom-main",
    )
) -> BloomClientInfo:
    """
    Validate and parse the X-Bloom-Client header.

    Args:
        x_bloom_client (str): The X-Bloom-Client header value

    Returns:
        BloomClientInfo: Parsed client information
    """
    if not x_bloom_client:
        raise errors.InvalidClientTypeError()

    return parse_bloom_client_header(x_bloom_client)


def validate_bloom_user_client(
    bloom_client: Annotated[BloomClientInfo, Depends(validate_bloom_client_header)],
) -> BloomClientInfo:
    """
    Validate that the Bloom client is a user client.

    Args:
        bloom_client (BloomClientInfo): The parsed Bloom client information

    Returns:
        BloomClientInfo: The validated user client information

    Raises:
        InvalidClienTypeError: If the client is not a user client
    """
    if not bloom_client.is_user_client():
        raise errors.InvalidClientTypeError()

    return bloom_client


def validate_is_not_bloom_user_client(
    bloom_client: Annotated[BloomClientInfo, Depends(validate_bloom_client_header)],
) -> BloomClientInfo:
    """
    Validate that the Bloom client is not a user client.
    """
    if bloom_client.is_user_client():
        raise errors.InvalidClientTypeError()

    return bloom_client


def validate_is_bloom_supplier_client(
    bloom_client: Annotated[BloomClientInfo, Depends(validate_bloom_client_header)],
) -> BloomClientInfo:
    """
    Validate that the Bloom client is a supplier client.
    """
    if not bloom_client.is_supplier_client():
        raise errors.InvalidClientTypeError()

    return bloom_client


def validate_is_bloom_seller_client(
    bloom_client: Annotated[BloomClientInfo, Depends(validate_bloom_client_header)],
) -> BloomClientInfo:
    """
    Validate that the Bloom client is a seller client.
    """
    if not bloom_client.is_seller_client():
        raise errors.InvalidClientTypeError()

    return bloom_client


def validate_is_bloom_admin_client(
    bloom_client: Annotated[BloomClientInfo, Depends(validate_bloom_client_header)],
) -> BloomClientInfo:
    """
    Validate that the Bloom client is an admin client.
    """
    if not bloom_client.is_admin_client():
        raise errors.InvalidClientTypeError()

    return bloom_client


def validate_is_either_bloom_supplier_or_seller_client(
    bloom_client: Annotated[BloomClientInfo, Depends(validate_bloom_client_header)],
) -> BloomClientInfo:
    """
    Validate that the Bloom client is either a supplier or seller client.
    """
    if not (bloom_client.is_supplier_client() or bloom_client.is_seller_client()):
        raise errors.InvalidClientTypeError()

    return bloom_client


auth_rate_limit = Depends(create_rate_limit_dependency("bloom_auth", "10/minute"))
api_rate_limit = Depends(create_rate_limit_dependency("bloom_api", "80/minute"))
medium_api_rate_limit = Depends(create_rate_limit_dependency("bloom_medium_api", "20/minute"))
upload_rate_limit = Depends(create_rate_limit_dependency("bloom_uploads", "5/minute"))
strict_rate_limit = Depends(create_rate_limit_dependency("bloom_strict", "5/minute"))
per_minute_rate_limit = Depends(create_rate_limit_dependency("bloom_per_minute", "1/minute"))
is_bloom_client = Depends(validate_bloom_client_header)
is_bloom_user_client = Depends(validate_bloom_user_client)
is_bloom_supplier_client = Depends(validate_is_bloom_supplier_client)
is_bloom_seller_client = Depends(validate_is_bloom_seller_client)
is_bloom_admin_client = Depends(validate_is_bloom_admin_client)
is_not_bloom_user_client = Depends(validate_is_not_bloom_user_client)
is_either_bloom_supplier_or_seller_client = Depends(validate_is_either_bloom_supplier_or_seller_client)


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
            metadata={
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
            metadata={"account_type": auth_state.type.value},
        )

    return auth_state


def require_eligible_seller_account(
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
            metadata={"account_type": auth_state.type.value},
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
            metadata={"account_type": auth_state.type.value},
        )

    return auth_state


def require_eligible_supplier_or_seller_account(
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
) -> AuthSessionState:
    """
    Dependency to ensure the authenticated account is a verified supplier or seller account.

    Args:
        auth_state (AuthSessionState): The authenticated session state

    Returns:
        AuthSessionState: The verified supplier or seller account session state
    """
    if not (auth_state.type.is_supplier() or auth_state.type.is_business()):
        raise errors.AccountIneligibleError(
            detail="Account is not a supplier or seller account",
            metadata={"account_type": auth_state.type.value},
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
            metadata={"account_type": auth_state.type.value},
        )

    return auth_state


def require_permissions(scopes: list[str], all_required: bool = True):
    """
    Create a dependency to require specific permissions for the authenticated account's type info.

    Args:
        required_scopes (list[str]): List of permission scopes required (e.g., ['users:read', 'products:create'])
        all_required (bool): Whether to require "all" of the permissions or "any" of them. Defaults to True.

    Returns:
        Dependency function that can be used with FastAPI routes
    """

    async def dependency(
        auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
        session: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> AuthSessionState:
        """
        Dependency function to check permissions.

        Args:
            auth_state (AuthSessionState): The authenticated session state
            session (AsyncSession): The database session

        Returns:
            AuthSessionState: The session state if permissions are granted

        Raises:
            InvalidPermissionError: If the required permissions are not granted
        """
        repo = AccountTypeInfoRepository(session)
        type_info = await repo.find_one_by(auth_state.type_info_id)

        if not type_info:
            raise errors.InvalidPermissionError(
                detail="Account type info not found",
            )

        if all_required:
            for scope in scopes:
                if not type_info.has_permission(scope):
                    raise errors.InvalidPermissionError(
                        detail=f"You are missing required permission scope {scope}",
                    )
        else:
            if not any(type_info.has_permission(scope) for scope in scopes):
                raise errors.InvalidPermissionError(
                    detail="You don't have any of the required permission scopes",
                )

        return auth_state

    return dependency


async def require_noauth_or_eligible_account(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_security_schemes()[0])],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthSessionState | None:
    """
    Dependency that requires an eligible account or an account that is not authenticated
    """

    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials

    decoded_token = security_service.decode_jwt_token(token)
    auth_state = security_service.get_token_data(decoded_token, AuthSessionState)

    token_service = TokenService(session=session)
    is_valid = await token_service.is_token_valid(token=token)

    if not is_valid:
        raise errors.InvalidTokenError()

    account_service = AccountService(session=session)
    account = await account_service.get_account_by(id=auth_state.id)

    if not account:
        raise errors.AccountNotFoundError()

    if not account.is_eligible():
        raise errors.AccountIneligibleError(
            metadata={
                "is_verified": account.is_verified,
                "is_active": account.is_active,
                "is_suspended": account.is_suspended,
                "is_locked": account.is_locked(),
            }
        )

    return auth_state
