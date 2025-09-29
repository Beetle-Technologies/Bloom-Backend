from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import (
    api_rate_limit,
    is_bloom_client,
    is_bloom_seller_client,
    is_bloom_supplier_client,
    is_either_bloom_supplier_or_seller_client,
    medium_api_rate_limit,
    require_eligible_seller_account,
    require_eligible_supplier_account,
    require_eligible_supplier_or_seller_account,
    require_noauth_or_eligible_account,
    requires_eligible_account,
)
from src.core.types import BloomClientInfo
from src.domain.schemas import AuthSessionState

router = APIRouter()


@router.get("/browse", dependencies=[api_rate_limit])
async def browse_catalog(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState | None, Depends(require_noauth_or_eligible_account)],
):
    """
    Browse the available catalog
    """
    pass


@router.post("/items", dependencies=[medium_api_rate_limit])
async def create_item(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_supplier_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_supplier_account)],
):
    """
    Create a new item in the catalog

    This is typically used by suppliers to add new products to their catalog.
    """
    pass


@router.get("/items/{item_fid}", dependencies=[api_rate_limit])
async def get_item(
    request: Request,
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to retrieve")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(requires_eligible_account)],
):
    """
    Get item details by item friendly ID
    """
    pass


@router.put("/items/{item_fid}", dependencies=[medium_api_rate_limit])
async def update_item(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_either_bloom_supplier_or_seller_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to update")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_supplier_or_seller_account)],
):
    """
    Update an item by its friendly ID
    """
    pass


@router.delete("/items/{item_fid}", dependencies=[medium_api_rate_limit])
async def delete_item(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_either_bloom_supplier_or_seller_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to delete")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_supplier_or_seller_account)],
):
    """
    Delete an item by its friendly ID
    """
    pass


@router.post("/items/{item_fid}/request", dependencies=[medium_api_rate_limit])
async def request_item(
    request: Request,
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to request")],
    request_client: Annotated[BloomClientInfo, is_bloom_seller_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_seller_account)],
):
    """
    Request an item by its friendly ID

    This is typically used by sellers to request stock from suppliers.
    """
    pass


@router.get("/items/{item_fid}/inventory", dependencies=[medium_api_rate_limit])
async def get_item_inventory(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_supplier_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to get inventory for")],
):
    """
    Get inventory details for an item by its friendly ID
    """
    pass


@router.get("/items/{item_fid}/inventory/history", dependencies=[medium_api_rate_limit])
async def get_item_inventory_history(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_supplier_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to get inventory history for")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_supplier_account)],
):
    """
    Get inventory history for an item by its friendly ID
    """
    pass


@router.post("/items/{item_fid}/inventory/adjust", dependencies=[medium_api_rate_limit])
async def adjust_item_inventory(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_supplier_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to adjust inventory for")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_supplier_account)],
):
    """
    Adjust inventory levels for an item by its friendly ID

    This can be used to increase or decrease stock levels.
    """
    pass
