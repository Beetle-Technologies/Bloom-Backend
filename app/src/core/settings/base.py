import base64
import os
import secrets
import warnings
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from dotenv import load_dotenv
from pydantic import AnyUrl, BeforeValidator, EmailStr, HttpUrl, PostgresDsn, RedisDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


def parse_cors(v: Any) -> list[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list):
        return v
    elif isinstance(v, str):
        return [v]
    raise ValueError(v)


def parse_string_separated_list(value: Any) -> list[str]:
    """Parse string separated list."""
    if isinstance(value, list):
        return value

    if not isinstance(value, str):
        raise ValueError(f"`{value}` expected to be list or string sperate list")

    value = value.replace("[", "").replace("]", "")
    return value.split(",")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    BASE_DIR: str = str(Path(__file__).resolve().parent.parent.parent.parent)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def JINJA_TEMPLATES_DIR(self) -> str:
        return os.path.join(self.BASE_DIR, "templates", "jinja")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def MJML_TEMPLATES_DIR(self) -> str:
        """Get MJML templates directory."""
        return os.path.join(self.BASE_DIR, "templates", "mjml")

    APP_NAME: str = "Bloom"
    APP_DESCRIPTION: str = "Bloom API for Businesses and Resellers"
    APP_VERSION: str = "0.1.0"
    OPENAPI_USERNAME: str = "admin"
    OPENAPI_PASSWORD: str = "changethis"
    OPENAPI_DOCS_URL: str = "/docs"
    OPENAPI_JSON_SCHEMA_URL: str = "/openapi.json"
    AUTH_SECRET_KEY: str = secrets.token_hex(64)
    FRONTEND_URL: HttpUrl | str = "http://localhost:3000"
    AUTH_OTP_SECRET_KEY: str = base64.b32encode(secrets.token_bytes(32)).decode()
    AUTH_OTP_MAX_AGE: int = 300  # 5 minutes
    AUTH_VERIFICATION_TOKEN_MAX_AGE: int = 60 * 60 * 24  # 24 hours
    BANKING_SECRET_KEY: str = secrets.token_urlsafe(32)
    AUTH_TOKEN_MAX_AGE: int = 60 * 60 * 8  # 8 hours
    AUTH_REMEMBER_TOKEN_MAX_AGE: int = 60 * 60 * 24 * 7  # 7 days
    MAX_LOGIN_FAILED_ATTEMPTS: int = 5
    MAX_LOGIN_RETRY_TIME: int = 60 * 30  # 30 minutes
    MAX_PASSWORD_RESET_TIME: int = 60 * 60 * 24  # 24 hours
    DOMAIN: str = "localhost"
    PORT: str
    V1_STR: str = "v1"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    LOAD_FIXTURES: bool = True
    RATE_LIMIT_PER_MINUTE: int = 15
    RATE_LIMIT_NAMESPACE: str = "bloom_base_throttler"

    CACHE_DEFAULT_TTL: int = 3600
    CACHE_KEY_PREFIX: str = "bloom_cache"
    CACHE_MEMORY_MAX_SIZE: int = 1000
    CACHE_MEMORY_CLEANUP_INTERVAL: int = 300  # 5 minutes
    CACHE_REDIS_DB: int = 1

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SERVER_URL(self) -> str:
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}:{self.PORT}"
        return f"https://{self.DOMAIN}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def API_V1_STR(self) -> str:
        return f"/api/{self.V1_STR}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SERVER_PORT(self) -> int:
        if self.ENVIRONMENT == "local":
            return int(self.PORT)
        return 443 if self.ENVIRONMENT == "production" else 80

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> RedisDsn:
        if self.REDIS_PASSWORD:
            return RedisDsn.build(
                scheme="redis",
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                password=self.REDIS_PASSWORD,
                path=f"{self.REDIS_DB}",
            )

        return RedisDsn.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            path=f"{self.REDIS_DB}",
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def THROTTLER_REDIS_URL(self) -> RedisDsn:
        if self.REDIS_PASSWORD:
            return RedisDsn.build(
                scheme="redis",
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                password=self.REDIS_PASSWORD,
                path="2",
            )

        return RedisDsn.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            path="2",
        )

    FILE_STORAGE_BACKEND: Literal["local", "s3", "cloudinary"] = "local"
    FILE_STORAGE_MEDIA_ROOT: str = str(Path(BASE_DIR) / "media")
    FILE_MAX_SIZE: int = 1024 * 1024 * 50  # 50 MB
    FILE_STORAGE_PRESIGNGED_EXPIRY_TIME: int = 7200  # 2 hour
    FILE_STORAGE_GENERATE_THUMBNAILS: bool = True
    FILE_STORAGE_S3_BUCKET_NAME: str | None = None
    FILE_STORAGE_S3_REGION_NAME: str | None = None
    FILE_STORAGE_S3_ACCESS_KEY_ID: str | None = None
    FILE_STORAGE_S3_SECRET_ACCESS_KEY: str | None = None
    FILE_STORAGE_S3_ENDPOINT_URL: str | None = None
    FILE_STORAGE_CLOUDINARY_CLOUD_NAME: str | None = None
    FILE_STORAGE_CLOUDINARY_API_KEY: str | None = None
    FILE_STORAGE_CLOUDINARY_API_SECRET: str | None = None
    FILE_STORAGE_CLOUDINARY_UPLOAD_PRESET: str | None = None

    CELERY_DEFAULT_TASKS_QUEUE: str = "bloom_default_tasks"
    CELERY_RECURRING_TASKS_QUEUE: str = "bloom_recurring_tasks"

    EMAIL_PROVIDER_TYPE: Literal["smtp", "ses"] = "smtp"

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_AUTH_SURPPORT: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str = "localhost"
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    AWS_SES_REGION_NAME: str = "us-east-1"
    AWS_SES_ACCESS_KEY_ID: str | None = None
    AWS_SES_SECRET_ACCESS_KEY: str | None = None

    EMAILS_FROM_NAME: str | None = None

    MAILER_DEFAULT_SENDER: EmailStr = "noreply@localhost.com"
    SUPPORT_EMAIL: EmailStr = "support@localhost.com"

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.APP_NAME
        return self

    def _check_email_config_for_backend(self, backend: str) -> None:
        if backend == "smtp" and self.SMTP_AUTH_SURPPORT and (not self.SMTP_USER or not self.SMTP_PASSWORD):
            raise ValueError("SMTP configuration is incomplete. Please check SMTP settings.")
        elif backend == "ses" and (
            not self.AWS_SES_REGION_NAME or not self.AWS_SES_ACCESS_KEY_ID or not self.AWS_SES_SECRET_ACCESS_KEY
        ):
            raise ValueError("AWS SES configuration is incomplete. Please check AWS SES settings.")

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", ' "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT in ["local", "staging"]:
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("AUTH_SECRET_KEY", self.AUTH_SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret("OPENAPI_PASSWORD", self.OPENAPI_PASSWORD)

        return self

    @model_validator(mode="after")
    def _enforce_file_storage_config(self) -> Self:
        if self.FILE_STORAGE_BACKEND not in ["local", "s3", "cloudinary"]:
            raise ValueError(f"Unsupported file storage backend: {self.FILE_STORAGE_BACKEND}")

        if self.FILE_STORAGE_BACKEND == "local":
            Path(self.FILE_STORAGE_MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
        elif self.FILE_STORAGE_BACKEND == "s3":
            if (
                not self.FILE_STORAGE_S3_BUCKET_NAME
                or not self.FILE_STORAGE_S3_REGION_NAME
                or not self.FILE_STORAGE_S3_ACCESS_KEY_ID
                or not self.FILE_STORAGE_S3_SECRET_ACCESS_KEY
            ):
                raise ValueError("S3 configuration is incomplete. Please check S3 settings.")
        elif self.FILE_STORAGE_BACKEND == "cloudinary":
            if (
                not self.FILE_STORAGE_CLOUDINARY_CLOUD_NAME
                or not self.FILE_STORAGE_CLOUDINARY_API_KEY
                or not self.FILE_STORAGE_CLOUDINARY_API_SECRET
            ):
                raise ValueError("Cloudinary configuration is incomplete. Please check Cloudinary settings.")

        return self

    @model_validator(mode="after")
    def _enforce_mailer_config(self) -> Self:
        if self.EMAIL_PROVIDER_TYPE not in ["smtp", "ses"]:
            raise ValueError(f"Unsupported email backend: {self.EMAIL_PROVIDER_TYPE}")

        self._check_email_config_for_backend(self.EMAIL_PROVIDER_TYPE)

        return self
