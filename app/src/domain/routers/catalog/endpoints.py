from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Path, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import (
    api_rate_limit,
    get_storage_service,
    is_bloom_client,
    is_bloom_seller_client,
    is_bloom_supplier_client,
    is_either_bloom_supplier_or_seller_client,
    medium_api_rate_limit,
    require_eligible_seller_account,
    require_eligible_supplier_account,
    require_eligible_supplier_or_seller_account,
    require_noauth_or_eligible_account,
)
from src.core.exceptions import errors
from src.core.helpers.request import parse_nested_query_params
from src.core.helpers.response import IResponseBase, build_json_response
from src.core.logging import get_logger
from src.core.types import BloomClientInfo
from src.domain.schemas import (
    DEFAULT_CATALOG_RETURN_FIELDS,
    AuthSessionState,
    CatalogBrowseParams,
    CatalogItemCreateRequest,
)
from src.domain.services.catalog_service import CatalogService
from src.libs.query_engine import GeneralPaginationRequest
from src.libs.storage import StorageService

from app.src.domain.enums.product import ProductStatus

logger = get_logger(__name__)


router = APIRouter()


@router.get("/browse", dependencies=[api_rate_limit], response_model=IResponseBase[dict[str, Any]])
async def browse_catalog(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState | None, Depends(require_noauth_or_eligible_account)],
) -> IResponseBase[dict[str, Any]]:
    """
    Browse the available catalog based on auth state.
    """
    try:
        parsed_params = parse_nested_query_params(request.query_params._dict)

        browse_params = CatalogBrowseParams(**parsed_params)

        pagination_filters: dict[str, Any] = {}
        if browse_params.filters:
            if browse_params.filters.status:
                pagination_filters["status__in"] = [s.value for s in browse_params.filters.status]
            if browse_params.filters.category:
                pagination_filters["category_id__in"] = browse_params.filters.category
            if browse_params.filters.min_price is not None:
                pagination_filters["price__gte"] = browse_params.filters.min_price
            if browse_params.filters.max_price is not None:
                pagination_filters["price__lte"] = browse_params.filters.max_price
            if browse_params.filters.search:
                pagination_filters["search_vector__search"] = browse_params.filters.search

            if not browse_params.filters.status:
                pagination_filters["status__eq"] = ProductStatus.ACTIVE

        pagination = GeneralPaginationRequest(
            limit=browse_params.limit,
            order_by=browse_params.order_by or ["-created_datetime"],
            filters=pagination_filters,
            include=browse_params.include or ["category", "currency"],
            include_total_count=browse_params.include_total_count,
            fields=browse_params.fields or ",".join(DEFAULT_CATALOG_RETURN_FIELDS),
            pagination_type=browse_params.pagination_type,
            cursor=browse_params.cursor,
            offset=browse_params.offset,
            page=browse_params.page,
        )

        catalog_service = CatalogService(session)
        result = await catalog_service.browse_catalog(auth_state, pagination)

        return build_json_response(data=result.to_dict(), message="Catalog retrieved successfully")
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.exception(f"src.domain.routers.catalog.browse_catalog:: Error browsing catalog: {e}")
        raise errors.ServiceError(
            detail="Failed to browse catalog",
            status=500,
        ) from e


@router.post(
    "/items",
    dependencies=[medium_api_rate_limit],
    response_model=IResponseBase[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
async def create_item(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_supplier_client],
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_supplier_account)],
    form_data: Annotated[CatalogItemCreateRequest, Form(..., media_type="multipart/form-data")],
):
    """
    Add a new item to the catalog

    This is typically used by suppliers to add new products to their catalog.
    """
    try:
        catalog_service = CatalogService(session)
        product = await catalog_service.create_catalog_item(form_data, auth_state, storage_service)

        return build_json_response(
            data={"product_id": str(product.id), "friendly_id": product.friendly_id},  # type: ignore
            message="Catalog item created successfully",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.exception(f"src.domain.routers.catalog.endpoints.create_item:: Error creating catalog item: {e}")
        raise errors.ServiceError(
            detail="Failed to create catalog item",
            status=500,
        ) from e


@router.get(
    "/items/{item_fid}",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[dict[str, dict[str, Any | list[dict[str, str]]]]],
)
async def get_item(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to retrieve")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState | None, Depends(require_noauth_or_eligible_account)],
) -> IResponseBase[dict[str, dict[str, Any | list[dict[str, str]]]]]:
    """
    Get item details by item friendly ID

    Matches on the catalog item to retrieve either it be a `Product` or `ProductItem` based on request client platform and auth state if any.
    """
    try:
        catalog_service = CatalogService(session)
        item, attachments = await catalog_service.get_catalog_item(item_fid, auth_state)

        return build_json_response(
            data={
                "item": {**item.model_dump(), "attachments": attachments},
            },
            message="Item retrieved successfully",
        )
    except errors.ServiceError as se:
        raise se
    except Exception as e:
        logger.exception(f"Error getting catalog item {item_fid}: {e}")
        raise errors.ServiceError(
            detail="Failed to retrieve catalog item",
            status=500,
        ) from e


@router.put("/items/{item_fid}", dependencies=[medium_api_rate_limit], status_code=status.HTTP_200_OK)
async def update_item(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_either_bloom_supplier_or_seller_client],
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to update")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_supplier_or_seller_account)],
):
    """
    Update an item by its friendly ID

    Matches on the catalog item to update based on `Product` supplier_account_id or `ProductItem` seller_account_id from the auth state.
    """
    pass


@router.delete("/items/{item_fid}", dependencies=[medium_api_rate_limit], status_code=status.HTTP_200_OK)
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


@router.post("/items/{item_fid}/request", dependencies=[medium_api_rate_limit], status_code=status.HTTP_200_OK)
async def request_item(
    request: Request,
    item_fid: Annotated[str, Path(..., description="The friendly ID of the item to request")],
    request_client: Annotated[BloomClientInfo, is_bloom_seller_client],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_state: Annotated[AuthSessionState, Depends(require_eligible_seller_account)],
):
    """
    Request an item by its friendly ID

    This is typically used by sellers to creating a product item and adding reserved stock from suppliers for a given seller account

    For now, it is going to implicitly request to create a product item for the seller account that dynamically allocates the inventory from the supplier's stock based on the supplier current unreserved inventory levels.
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


@router.post("/items/{item_fid}/inventory/adjust", dependencies=[medium_api_rate_limit], status_code=status.HTTP_200_OK)
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
