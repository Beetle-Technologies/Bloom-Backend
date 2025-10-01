from fastapi_problem.cors import CorsConfiguration
from fastapi_problem.handler import new_exception_handler
from src.core.config import settings

eh = new_exception_handler(
    cors=CorsConfiguration(
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    ),
    documentation_uri_template=f"{settings.server_url}/errors/{{type}}",
    strict_rfc9457=True,
)
