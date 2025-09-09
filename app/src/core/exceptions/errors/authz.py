from fastapi_problem.error import ForbiddenProblem


class AuthorizationError(ForbiddenProblem):
    """
    An base error indicating that authorization has failed.
    """

    type_ = "authorization_error"
    title = "Invalid Authorization"


class InvalidPermissionError(AuthorizationError):
    """
    An error indicating that the user does not have the required permissions.
    """

    type_ = "invalid_permission_error"
    title = "Invalid Permission"
