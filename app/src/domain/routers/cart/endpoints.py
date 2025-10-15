from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Request, status
from fastapi_problem.error import StatusProblem
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import api_rate_limit, is_bloom_user_client, require_eligible_user_account
from src.core.exceptions import errors
from src.core.helpers.response import IResponseBase, build_json_response
from src.core.logging import get_logger
from src.core.types import BloomClientInfo
from src.domain.models.cart_item import CartItem
from src.domain.schemas import AddToCartRequest, AuthSessionState, UpdateCartItemRequest
from src.domain.services.cart_service import CartService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/",
    dependencies=[api_rate_limit],
    status_code=status.HTTP_200_OK,
    response_model=IResponseBase[dict[str, Any]],
    operation_id="add_to_cart",
)
async def add_to_cart(
    request: Request,  # noqa: ARG001
    request_client: Annotated[BloomClientInfo, is_bloom_user_client],  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
    add_data: Annotated[AddToCartRequest, Body(..., description="Data for adding an item to the cart")],
):
    """
    Add a catalog item to the cart.

    This is used by the user type to add items to the cart if the item is not already present.

    It dynamically creates a cart if one does not exist for the user.
    """
    try:
        cart_service = CartService(session)
        cart_item = await cart_service.add_to_cart(add_data.item_fid, add_data.quantity, auth_state)
        return build_json_response(data=cart_item, message="Item added to cart successfully")
    except errors.ServiceError as se:
        raise se
    except StatusProblem as sp:
        raise sp
    except Exception as e:
        logger.exception(f"src.domain.routers.cart.endpoints.add_to_cart:: Error adding to cart: {e}")
        raise errors.ServiceError("Failed to add item to cart")


@router.get(
    "/{cart_fid}",
    dependencies=[api_rate_limit],
    status_code=status.HTTP_200_OK,
    response_model=IResponseBase[dict[str, Any]],
    operation_id="get_cart",
)
async def get_cart(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_user_client],
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
) -> IResponseBase[dict[str, Any]]:
    """
    Retrieve a specific cart by its friendly ID.

    This is used by the user type to view a specific shopping cart.
    """
    try:
        cart_service = CartService(session)
        cart = await cart_service.get_cart_by_friendly_id(cart_fid, auth_state)
        if not cart:
            raise errors.NotFoundError("Cart not found")

        return build_json_response(data=cart.model_dump(), message="Cart retrieved successfully")
    except errors.ServiceError as se:
        raise se
    except StatusProblem as sp:
        raise sp
    except Exception as e:
        logger.exception(f"src.domain.routers.cart.endpoints.get_cart:: Error getting cart {cart_fid}: {e}")
        raise errors.ServiceError("Failed to retrieve cart")


@router.delete(
    "/{cart_fid}",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[None],
    status_code=status.HTTP_200_OK,
    operation_id="clear_cart",
)
async def clear_cart(
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart to clear")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
) -> IResponseBase[None]:
    """
    Clear all items from a specific cart by its friendly ID.

    This is used by the user type to clear their shopping cart.
    """
    try:
        cart_service = CartService(session)
        cleared = await cart_service.clear_cart(cart_fid, auth_state)
        if not cleared:
            raise errors.NotFoundError("Cart not found")

        return build_json_response(data=None, message="Cart cleared successfully")
    except errors.ServiceError as se:
        raise se
    except StatusProblem as sp:
        raise sp
    except Exception as e:
        logger.exception(f"src.domain.routers.cart.endpoints.clear_cart:: Error clearing cart {cart_fid}: {e}")
        raise errors.ServiceError("Failed to clear cart")


@router.put(
    "/{cart_fid}/items/{item_fid}",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[CartItem],
    status_code=status.HTTP_200_OK,
    operation_id="update_cart_item",
)
async def update_cart_item(
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the cart item to update")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
    update_data: Annotated[UpdateCartItemRequest, Body(..., description="The data to update the cart item")],
) -> IResponseBase[CartItem]:
    """
    Update the quantity of an item in the cart.

    This is used by the user type to update the quantity of items in their shopping cart.
    """
    try:
        cart_service = CartService(session)
        updated_item = await cart_service.update_cart_item(cart_fid, item_fid, update_data.quantity, auth_state)
        if not updated_item:
            raise errors.NotFoundError("Cart item not found")

        return build_json_response(data=updated_item, message="Cart item updated successfully")
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.exception(f"Error updating cart item {item_fid}: {e}")
        raise errors.ServiceError("Failed to update cart item")


@router.delete(
    "/{cart_fid}/items/{item_fid}",
    dependencies=[api_rate_limit],
    status_code=status.HTTP_200_OK,
    response_model=IResponseBase[None],
    operation_id="remove_from_cart",
)
async def remove_from_cart(
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the cart item to remove")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_user_account)],
) -> IResponseBase[None]:
    """
    Remove an item from the cart.

    This is used by the user type to remove items from their shopping cart.
    """
    try:
        cart_service = CartService(session)
        removed = await cart_service.remove_from_cart(cart_fid, item_fid, auth_state)
        if not removed:
            raise errors.NotFoundError("Cart item not found")

        return build_json_response(data=None, message="Item removed from cart successfully")
    except errors.ServiceError as se:
        raise se
    except StatusProblem as sp:
        raise sp
    except Exception as e:
        logger.exception(
            f"src.domain.routers.cart.endpoints.remove_from_cart:: Error removing from cart {item_fid}: {e}"
        )
        raise errors.ServiceError("Failed to remove item from cart")
