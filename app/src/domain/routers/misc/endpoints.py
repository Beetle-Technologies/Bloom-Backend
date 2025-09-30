from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database.session import get_db_session
from src.core.dependencies import api_rate_limit, is_bloom_client
from src.core.exceptions import errors
from src.core.helpers.request import parse_nested_query_params
from src.core.helpers.response import IResponseBase, build_json_response
from src.core.logging import get_logger
from src.core.types import BloomClientInfo
from src.domain.repositories.country_repository import CountryRepository
from src.domain.repositories.currency_repository import CurrencyRepository
from src.libs.query_engine import GeneralPaginationRequest

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/currencies",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[dict[str, Any]],
)
async def get_currencies(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IResponseBase[dict[str, Any]]:
    """
    Get paginated list of currencies with search.
    """
    try:
        parsed_params = parse_nested_query_params(request.query_params._dict)
        pagination = GeneralPaginationRequest(**parsed_params)

        if not pagination.filters:
            pagination.filters = {}
        pagination.filters["is_active__eq"] = True

        if pagination.filters["search"]:
            pagination.filters["search_vector__search"] = pagination.filters.pop("search")

        currency_repo = CurrencyRepository(session)
        result = await currency_repo.find(pagination=pagination)

        return build_json_response(data=result.to_dict(), message="Currencies retrieved successfully")
    except errors.ServiceError as se:
        raise se
    except Exception:
        logger.exception("src.domain.routers.misc.endpoints.get_currencies:: Error getting currencies: {e}")
        raise errors.ServiceError("Failed to get currencies", status=500)


@router.get(
    "/countries",
    dependencies=[api_rate_limit],
    response_model=IResponseBase[dict[str, Any]],
)
async def get_countries(
    request: Request,
    request_client: Annotated[BloomClientInfo, is_bloom_client],  # noqa: ARG001
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IResponseBase[dict[str, Any]]:
    """
    Get paginated list of countries with search.
    """
    try:
        parsed_params = parse_nested_query_params(request.query_params._dict)
        pagination = GeneralPaginationRequest(**parsed_params)

        if not pagination.filters:
            pagination.filters = {}
        pagination.filters["is_active__eq"] = True

        if pagination.filters["search"]:
            pagination.filters["search_vector__search"] = pagination.filters.pop("search")

        country_repo = CountryRepository(session)
        result = await country_repo.find(pagination=pagination)

        return build_json_response(data=result.to_dict(), message="Countries retrieved successfully")
    except errors.ServiceError as se:
        raise se
    except Exception:
        logger.exception("src.domain.routers.misc.endpoints.get_countries:: Error getting countries: {e}")
        raise errors.ServiceError("Failed to get countries", status=500)
