from typing import Optional

from fastapi import status
from src.core.exceptions import errors


class QueryEngineError(errors.ServiceError):
    """Base error for query engine related issues"""

    type_ = "query_engine_error"
    title = "Query Engine Error"
    detail = "An error occurred in the query engine."
    status = status.HTTP_400_BAD_REQUEST


class InvalidFieldError(QueryEngineError):
    """Error raised when an invalid field is specified in select or filters"""

    title = "Invalid Field Error"
    detail = "One or more specified fields do not exist in the model."

    def __init__(
        self,
        invalid_fields: Optional[list[str]] = None,
        valid_fields: Optional[list[str]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.invalid_fields = invalid_fields or []
        self.valid_fields = valid_fields or []

        if invalid_fields and valid_fields:
            self.detail = (
                f"Invalid fields specified: {', '.join(invalid_fields)}. "
                f"Valid selectable fields are: {', '.join(valid_fields)}"
            )
        elif invalid_fields:
            self.detail = f"Invalid fields specified: {', '.join(invalid_fields)}"


class InvalidFilterError(QueryEngineError):
    """Error raised when an invalid filter is provided"""

    title = "Invalid Filter Error"
    detail = "One or more filters are invalid or malformed."


class EntityNotFoundError(QueryEngineError):
    """Error raised when a single entity query returns no results"""

    title = "Entity Not Found"
    detail = "The requested entity could not be found."
    status = status.HTTP_404_NOT_FOUND


class MultipleEntitiesFoundError(QueryEngineError):
    """Error raised when a single entity query returns multiple results"""

    title = "Multiple Entities Found"
    detail = "Expected single entity but multiple entities were found."
