import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_problem.handler import add_exception_handler
from src.core.config import settings
from src.core.database.session import engine
from src.core.database.utils import register_triggers
from src.core.exceptions.handler import eh
from src.core.middlewares import (
    RequestThrottlerMiddleware,
    RequestUtilsMiddleware,
)
from src.core.openapi import OpenAPI
from src.domain.routers import account_router, auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    try:
        await register_triggers()

        yield
    finally:
        try:
            await engine.dispose()
        except TimeoutError:
            print("Ungraceful shutdown")
        except asyncio.CancelledError:
            print("Graceful shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    redoc_url=None,
    openapi_url=None,
)

add_exception_handler(app, eh, generic_swagger_defaults=False)

openapi = OpenAPI()


app.mount(
    "/static",
    StaticFiles(directory=Path.joinpath(settings.BASE_DIR, "static")),
    name="static",
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.ENVIRONMENT in ["production"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
    )
    app.add_middleware(HTTPSRedirectMiddleware)


app.add_middleware(GZipMiddleware, compresslevel=5)
app.add_middleware(RequestUtilsMiddleware)
app.add_middleware(RequestThrottlerMiddleware)

# Routers (V1)
app.include_router(
    account_router, prefix=f"{settings.api_v1_str}/accounts", tags=["Accounts"]
)
app.include_router(auth_router, prefix=f"{settings.api_v1_str}/auth", tags=["Auth"])

openapi.setup(app)
