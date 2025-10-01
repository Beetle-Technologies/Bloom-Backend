from fastapi import status
from fastapi_problem.error import StatusProblem


class ServiceError(StatusProblem):
    """
    This error is raised when a service-related error occurs.
    """

    type_ = "service_error"
    title = "Service Error"
    detail = "An error occurred while processing your request."
    status = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail=None, **kwargs):
        super().__init__(detail=detail or self.detail, **kwargs)


class NotFoundError(StatusProblem):
    """
    This error is raised when a requested resource is not found.
    """

    type_ = "not_found_error"
    title = "Resource Not Found"
    detail = "The requested resource could not be found."
    status = status.HTTP_404_NOT_FOUND

    def __init__(self, detail=None, **kwargs):
        super().__init__(detail=detail or self.detail, **kwargs)


class InternalServerError(StatusProblem):
    """
    This error is raised when an unexpected internal server error occurs.
    """

    type_ = "internal_server_error"
    title = "Internal Server Error"
    detail = "An unexpected error occurred on the server."
    status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail=None, **kwargs):
        super().__init__(detail=detail or self.detail, **kwargs)


class UnauthorizedError(StatusProblem):
    """
    This error is raised when a request is unauthorized.
    """

    type_ = "unauthorized_error"
    title = "Authorization Required"
    detail = "You are not authorized to access this resource."
    status = status.HTTP_401_UNAUTHORIZED

    def __init__(self, detail=None, **kwargs):
        super().__init__(detail=detail or self.detail, **kwargs)


class RateLimitExceededError(StatusProblem):
    """
    This error is raised when a client exceeds the allowed rate limit.
    """

    type_ = "rate_limit_exceeded"
    title = "Rate Limit Exceeded"
    detail = "You have exceeded your request rate limit."
    status = status.HTTP_429_TOO_MANY_REQUESTS

    def __init__(self, detail=None, **kwargs):
        super().__init__(detail=detail or self.detail, **kwargs)
