from fastapi import Request, Response
from src.core.config import settings
from src.core.exceptions import errors
from src.core.security import verify_csrf_token
from starlette.middleware.base import BaseHTTPMiddleware


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        secret_key: str = settings.CSRF_SECRET_KEY,
    ) -> None:
        super().__init__(app)
        self.secret_key = secret_key
        self.safe_methods = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in self.safe_methods:
            response = await call_next(request)
            return response
        else:
            # NOTE: I am using the cookies as the source of truth for CSRF tokens
            token = request.cookies.get("X-CSRF-Token")
            signature = request.cookies.get("X-CSRF-Signature")

            if not token or not signature:
                raise errors.CSRFError()

            is_valid_token = verify_csrf_token(token, signature, self.secret_key)

            if not is_valid_token:
                raise errors.CSRFError(detail="Expired CSRF Token")

            response = await call_next(request)

            return response
