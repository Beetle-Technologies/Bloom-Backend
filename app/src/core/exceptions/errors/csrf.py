from fastapi_problem.error import UnauthorisedProblem


class CSRFError(UnauthorisedProblem):
    """
    A base error indicating that the CSRF token is invalid or missing.
    """

    type_ = "csrf_error"
    title = "Invalid CSRF token"
    detail = "Please provide a valid CSRF token."
