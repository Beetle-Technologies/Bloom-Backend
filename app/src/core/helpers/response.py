from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataType = TypeVar("DataType")
T = TypeVar("T")


class IResponseBase(BaseModel, Generic[T]):
    """
    Base response model for API responses.\n

    Attributes:\n
        message (str | None): A message providing additional information about the response.
        data (T | None): The main data payload of the response, which can be of any type `T`.
        meta (dict[str, Any] | None): Optional metadata about the response, such as pagination information or other relevant details.
    """

    message: str | None = None
    data: T | None = None
    meta: dict[str, Any] | None = None


def build_json_response_content(
    data: DataType,
    message: str | None = None,
    meta: dict[str, Any] | None = None,
) -> IResponseBase[DataType]:
    """
    Creates a standardized API response.

    Args:\n
        data (DataType): The main data payload of the response.
        message (str | None): An optional message providing additional information about the response.
        meta (dict[str, Any] | None): Optional metadata about the response

    Returns:
        IResponseBase[DataType]: An instance of `IResponseBase` containing the provided data, message, and metadata.
    """

    return IResponseBase[DataType](
        message=message,
        data=data,
        meta=meta,
    )
