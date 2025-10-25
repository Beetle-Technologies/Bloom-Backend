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


@router.get(
    "/",
    dependencies=[api_rate_limit],
    operation_id="list_orders",
)
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


@router.post(
    "/checkout",
    dependencies=[api_rate_limit],
    operation_id="checkout_cart",
)
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


@router.get(
    "/{order_fid}",
    dependencies=[api_rate_limit],
    operation_id="get_order_details",
)
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


@router.delete(
    "/{order_fid}",
    dependencies=[api_rate_limit],
    operation_id="cancel_order",
)
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


@router.get(
    "/{order_fid}/invoice",
    dependencies=[api_rate_limit],
    operation_id="get_order_invoice",
)
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


router.get(
    "/analytics/stats",
    dependencies=[api_rate_limit],
    operation_id="get_orders_analytics_stats",
)


async def get_orders_analytics_stats(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get orders analytics statistics for the authenticated account
    """
    pass


@router.get(
    "/{item_fid}/analytics/stats",
    dependencies=[api_rate_limit],
    operation_id="get_order_item_analytics_stats",
)
async def get_order_item_analytics_stats(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to retrieve analytics for")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get analytics statistics for a specific order item by item friendly ID
    """
    pass


@router.get(
    "/analytics/trends",
    dependencies=[api_rate_limit],
    operation_id="get_orders_analytics_trends",
)
async def get_orders_analytics_trends(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get orders analytics trends for the authenticated account
    """
    pass


@router.get(
    "/{item_fid}/analytics/trends",
    dependencies=[api_rate_limit],
    operation_id="get_order_item_analytics_trends",
)
async def get_order_item_analytics_trends(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to retrieve analytics for")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get analytics trends for a specific order item by item friendly ID
    """
    pass


@router.get(
    "/analytics/top_items",
    dependencies=[api_rate_limit],
    operation_id="get_orders_analytics_top_items",
)
async def get_orders_analytics_top_items(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get top ordered items analytics for the authenticated account
    """
    pass


@router.get(
    "/analytics/customer_activity",
    dependencies=[api_rate_limit],
    operation_id="get_orders_analytics_customer_activity",
)
async def get_orders_analytics_customer_activity(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get customer activity analytics for the authenticated account
    """
    pass


@router.get(
    "/{item_fid}/analytics/customer_activity",
    dependencies=[api_rate_limit],
    operation_id="get_order_item_analytics_customer_activity",
)
async def get_order_item_analytics_customer_activity(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to retrieve analytics for")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get customer activity analytics for a specific order item by item friendly ID
    """
    pass
