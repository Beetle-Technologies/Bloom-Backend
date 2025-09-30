from pydantic import BaseModel, Field, PositiveInt
from src.core.helpers.schema import optional
from src.core.types import GUID


class CartCreate(BaseModel):
    """
    Schema for creating a cart.
    """

    account_type_info_id: GUID


@optional
class CartUpdate(BaseModel):
    """
    Schema for updating a cart.
    """

    account_type_info_id: GUID | None = None
    session_id: str | None = None


class CartItemCreate(BaseModel):
    """
    Schema for creating a cart item.
    """

    cart_id: GUID
    cartable_type: str
    cartable_id: GUID
    quantity: PositiveInt = Field(gt=0)


@optional
class CartItemUpdate(CartItemCreate):
    """
    Schema for updating a cart item.
    """

    pass


class AddToCartRequest(BaseModel):
    """
    Schema for adding an item to the cart.
    """

    item_fid: str
    quantity: PositiveInt = Field(gt=0)
