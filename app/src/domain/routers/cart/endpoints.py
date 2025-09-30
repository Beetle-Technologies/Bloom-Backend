from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import api_rate_limit, is_bloom_user_client, require_eligible_user_account
from src.core.types import BloomClientInfo
from src.domain.schemas import AuthSessionState

router = APIRouter()


@router.post(
    "/",
    dependencies=[api_rate_limit],
    status_code=status.HTTP_200_OK,
)
async def add_to_cart():
    """
    Add a catalog item to the cart.

    This is used by the user type to add items to the cart if the item is not already present.

    It dynamically creates a cart if one does not exist for the user.
    """
    pass


@router.get(
    "/{cart_fid}",
    dependencies=[api_rate_limit],
)
async def get_cart(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_user_client],
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
):
    """
    Retrieve a specific cart by its friendly ID.

    This is used by the user type to view a specific shopping cart.
    """
    pass


@router.delete(
    "/{cart_fid}",
    dependencies=[api_rate_limit],
    status_code=status.HTTP_200_OK,
)
async def clear_cart(
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart to clear")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
):
    """
    Clear all items from a specific cart by its friendly ID.

    This is used by the user type to clear their shopping cart.
    """
    pass


@router.put(
    "/{cart_fid}/items/{item_fid}",
    dependencies=[api_rate_limit],
    status_code=status.HTTP_200_OK,
)
async def update_cart_item(
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the cart item to update")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
):
    """
    Update the quantity of an item in the cart.

    This is used by the user type to update the quantity of items in their shopping cart.
    """
    pass


@router.delete(
    "/{cart_fid}/items/{item_fid}",
    dependencies=[api_rate_limit],
    status_code=status.HTTP_200_OK,
)
async def remove_from_cart(
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the cart item to remove")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
):
    """
    Remove an item from the cart.

    This is used by the user type to remove items from their shopping cart.
    """
    pass
