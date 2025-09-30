from typing import Annotated

from fastapi import APIRouter, Path

router = APIRouter()


@router.get("/")
async def get_carts():
    """
    Retrieve the current user's cart.

    This is used by the user type to view their shopping cart.
    """
    pass


@router.post("/items")
async def add_to_cart():
    """
    Add a catalog item to the cart.

    This is used by the user type to add items to the cart if the item is not already present.

    It dynamically creates a cart if one does not exist for the user.
    """
    pass


@router.get("/{cart_fid}")
async def get_cart(cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")]):
    """
    Retrieve a specific cart by its friendly ID.

    This is used by the user type to view a specific shopping cart.
    """
    pass


@router.put("/{cart_fid}/items/{item_fid}")
async def update_cart_item(
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the cart item to update")],
):
    """
    Update the quantity of an item in the cart.

    This is used by the user type to update the quantity of items in their shopping cart.
    """
    pass


@router.delete("/{cart_fid}/items/{item_fid}")
async def remove_from_cart(
    cart_fid: Annotated[str, Path(..., description="The friendly ID of the cart")],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the cart item to remove")],
):
    """
    Remove an item from the cart.

    This is used by the user type to remove items from their shopping cart.
    """
    pass
