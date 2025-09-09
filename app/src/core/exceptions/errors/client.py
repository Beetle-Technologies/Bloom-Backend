from fastapi import status
from fastapi_problem.error import StatusProblem


class InvalidClientHeaderError(StatusProblem):
    """
    This error is raised when the X-Bloom-Client header format is invalid.
    """

    type_ = "invalid_client_header"
    title = "Invalid Client Header"
    detail = "The X-Bloom-Client header format is invalid or missing required parameters."
    status = status.HTTP_400_BAD_REQUEST


class UnsupportedPlatformError(StatusProblem):
    """
    This error is raised when an unsupported platform is specified in the client header.
    """

    type_ = "unsupported_platform"
    title = "Unsupported Platform"
    detail = "The specified platform is not supported."
    status = status.HTTP_400_BAD_REQUEST


class UnsupportedAppError(StatusProblem):
    """
    This error is raised when an unsupported app is specified in the client header.
    """

    type_ = "unsupported_app"
    title = "Unsupported App"
    detail = "The specified app is not supported."
    status = status.HTTP_400_BAD_REQUEST
