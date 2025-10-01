from fastapi import status
from fastapi_problem.error import StatusProblem


class DatabaseError(StatusProblem):
    """
    An base error indicating that a database operation failed.
    """

    type_ = "database_error"
    title = "Database error"
    status = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "An error occurred while interacting with the database."

    def __init__(self, detail=None, **kwargs):
        super().__init__(detail=detail or self.detail, **kwargs)
