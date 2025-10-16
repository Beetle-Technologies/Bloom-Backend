from typing import Annotated, Any

from fastapi import APIRouter, Path
from src.core.helpers.response import IResponseBase

router = APIRouter()


@router.get(
    "/{store_id}",
    response_model=IResponseBase[dict[str, Any]],
    operation_id="get_store_details",
)
async def get_store(
    store_id: Annotated[str, Path(..., description="The ID of the store to retrieve")],
):
    """
    Retrieve details of a specific store by the given store ID
    """

    pass
