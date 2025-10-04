from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import (
    api_rate_limit,
    is_bloom_client,
    is_bloom_user_client,
    require_eligible_user_account,
    requires_eligible_account,
)
from src.core.types import BloomClientInfo
from src.domain.schemas import AuthSessionState

router = APIRouter()


@router.get("/", dependencies=[api_rate_limit])
async def list_orders(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    List orders for the authenticated account
    """
    pass


@router.post("/checkout", dependencies=[api_rate_limit])
async def checkout_cart(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_user_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
):
    """
    Checkout the current user's cart and create an order
    """
    pass


@router.get("/{order_fid}")
async def get_order(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    order_fid: Annotated[str, Path(..., description="The friendly ID of the order to retrieve")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get order details by order friendly ID
    """
    pass


@router.delete("/{order_fid}", dependencies=[api_rate_limit])
async def cancel_order(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_user_client],
    order_fid: Annotated[str, Path(..., description="The friendly ID of the order to delete")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
):
    """
    Cancel an order by order friendly ID if it hasn't been confirmed yet
    """
    pass


@router.get("/{order_fid}/invoice", dependencies=[api_rate_limit])
async def get_order_invoice(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_user_client],
    order_fid: Annotated[str, Path(..., description="The friendly ID of the order to get the invoice for")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
):
    """
    Get the invoice for a specific order by order friendly ID
    """
    pass
