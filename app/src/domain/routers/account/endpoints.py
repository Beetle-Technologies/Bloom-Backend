from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import api_rate_limit, is_bloom_client, requires_eligible_account
from src.core.types import BloomClientInfo
from src.domain.schemas import AuthSessionState

router = APIRouter()


@router.get("/me", dependencies=[api_rate_limit])
async def me(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    auth_state: Annotated[AuthSessionState, requires_eligible_account],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get current user information
    """
    pass


@router.put("/me", dependencies=[api_rate_limit])
async def update_me():
    """
    Update current user information
    """
    pass


@router.delete("/me", dependencies=[api_rate_limit])
async def delete_me():
    """
    Delete current user account
    """
    pass


@router.get("/me/preferences", dependencies=[api_rate_limit])
async def get_preferences():
    """
    Get current user preferences
    """
    pass


@router.put("/me/preferences", dependencies=[api_rate_limit])
async def update_preferences():
    """
    Update current user preferences
    """
    pass


@router.get("/me/notifications", dependencies=[api_rate_limit])
async def get_notifications():
    """
    Get current user notifications
    """
    pass
