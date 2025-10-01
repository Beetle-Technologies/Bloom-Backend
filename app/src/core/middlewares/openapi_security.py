import base64
import json

from fastapi import Request, Response
from src.core.config import settings
from src.core.exceptions import errors
from src.core.logging import get_logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = get_logger(__name__)


class OpenAPISecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to secure OpenAPI documentation endpoints with basic authentication.
    """

    def __init__(
        self, app: ASGIApp, *, username: str = settings.OPENAPI_USERNAME, password: str = settings.OPENAPI_PASSWORD
    ) -> None:
        super().__init__(app)

        self.username = username
        self.password = password

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in [settings.OPENAPI_DOCS_URL, settings.OPENAPI_JSON_SCHEMA_URL]:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return self._unauthorized_response()

            try:
                auth_type, auth_value = auth_header.split()
                if auth_type.lower() != "basic":
                    return self._unauthorized_response()

                decoded = base64.b64decode(auth_value).decode()
                username, password = decoded.split(":")

                if username != self.username or password != self.password:
                    return self._unauthorized_response()

                response = await call_next(request)
                return response
            except Exception:
                logger.error(f"{__name__}.dispatch:: Invalid Authorization header format", exc_info=True)
                return self._unauthorized_response()

        return await call_next(request)

    def _unauthorized_response(self):
        error = errors.UnauthorizedError()
        return Response(
            content=json.dumps(error.marshal(uri=f"{settings.server_url}/errors/{{type}}", strict=True)),
            status_code=error.status,
            headers={
                "content-type": "application/problem+json",
                "WWW-Authenticate": 'Basic realm="OpenAPI Documentation"',
                **(error.headers or {}),
            },
        )
