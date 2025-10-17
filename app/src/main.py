import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_problem.handler import add_exception_handler
from src.core.config import settings
from src.core.database.session import engine
from src.core.database.utils import register_triggers
from src.core.exceptions.handler import eh
from src.core.logging import get_logger, get_logging_config, setup_exception_logging, setup_logging
from src.core.middlewares import RequestThrottlerMiddleware, RequestUtilsMiddleware
from src.core.openapi import OpenAPI
from src.domain.routers import (
    account_router,
    admin_router,
    attachment_router,
    auth_router,
    cart_router,
    catalog_router,
    health_router,
    misc_router,
    order_router,
    stores_router,
)

if settings.ENVIRONMENT in ["staging", "production"]:
    setup_logging(config_override=get_logging_config())
    setup_exception_logging()


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Application lifespan manager with enhanced logging.
    """
    try:
        logger.info("Application startup initiated", extra={"event_type": "app_startup_start"})

        await register_triggers()

        logger.info(
            "Application startup completed successfully",
            extra={
                "event_type": "app_startup_complete",
                "environment": settings.ENVIRONMENT,
                "app_version": settings.APP_VERSION,
            },
        )

        yield

    except Exception as exc:
        logger.error(
            "Application startup failed",
            exc_info=True,
            extra={
                "event_type": "app_startup_failed",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        )
        raise
    finally:
        try:
            logger.info(
                "Application shutdown initiated",
                extra={"event_type": "app_shutdown_start"},
            )

            await engine.dispose()
            logger.info("Database engine disposed", extra={"event_type": "db_engine_disposed"})

            logger.info(
                "Application shutdown completed",
                extra={"event_type": "app_shutdown_complete"},
            )

        except TimeoutError:
            logger.warning(
                "Database shutdown timeout - ungraceful shutdown",
                extra={"event_type": "db_shutdown_timeout"},
            )
        except asyncio.CancelledError:
            logger.info(
                "Application shutdown cancelled - graceful shutdown",
                extra={"event_type": "app_shutdown_cancelled"},
            )
        except Exception as exc:
            logger.error(
                "Error during application shutdown",
                exc_info=True,
                extra={
                    "event_type": "app_shutdown_error",
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                },
            )


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=settings.OPENAPI_DOCS_URL,
    openapi_url=settings.OPENAPI_JSON_SCHEMA_URL,
    redoc_url=None,
)

add_exception_handler(app, eh)


openapi = OpenAPI()


app.mount(
    "/static",
    StaticFiles(directory=Path(settings.BASE_DIR) / "static"),
    name="static",
)

app.mount(
    "/media",
    StaticFiles(directory=Path(settings.FILE_STORAGE_MEDIA_ROOT)),
    name="media",
)

# Middlewares
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


if settings.ENVIRONMENT in ["production"]:
    app.add_middleware(HTTPSRedirectMiddleware)


app.add_middleware(GZipMiddleware, compresslevel=5)
app.add_middleware(RequestUtilsMiddleware)
app.add_middleware(RequestThrottlerMiddleware)


# Routers (V1)
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin"])
app.include_router(account_router, prefix=f"{settings.API_V1_STR}/accounts", tags=["Accounts"])
app.include_router(attachment_router, prefix=f"{settings.API_V1_STR}/attachments", tags=["Attachments"])
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(catalog_router, prefix=f"{settings.API_V1_STR}/catalog", tags=["Catalog"])
app.include_router(cart_router, prefix=f"{settings.API_V1_STR}/cart", tags=["Cart"])
app.include_router(health_router, prefix="/health", include_in_schema=False)
app.include_router(misc_router, prefix=f"{settings.API_V1_STR}/misc", tags=["Miscellaneous"])
app.include_router(order_router, prefix=f"{settings.API_V1_STR}/orders", tags=["Orders"])
app.include_router(stores_router, prefix=f"{settings.API_V1_STR}/stores", tags=["Stores"])


openapi.setup(app)
