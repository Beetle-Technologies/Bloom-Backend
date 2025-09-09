from typing import Any, Dict, Union

from .enums import PaginationType
from .schemas import GeneralPaginationResponse, KeysetPaginationResponse, OffsetPaginationResponse


def format_pagination_data(
    pagination_response: Union[GeneralPaginationResponse, OffsetPaginationResponse, KeysetPaginationResponse],
    pagination_type: PaginationType | None = None,
) -> Dict[str, Any]:
    """
    Format pagination response data for the frontend pagination component.

    Args:
        pagination_response: The pagination response from the paginator
        pagination_type: The type of pagination used (optional, will be inferred if not provided)

    Returns:
        Dictionary containing pagination data for the template
    """
    if isinstance(pagination_response, GeneralPaginationResponse):
        return pagination_response.to_dict()

    general_response = GeneralPaginationResponse.from_existing_response(pagination_response)
    return general_response.to_dict()
