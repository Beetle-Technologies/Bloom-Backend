from typing import Any

from src.core.config import settings
from src.core.logging import get_logger
from src.libs.mailer.interface import EmailProvider
from src.libs.mailer.providers.smtp import SMTPProvider
from src.libs.mailer.schemas import SMTPConfiguration

logger = get_logger(__name__)


class MailerFactory:
    """
    Factory for creating email providers.
    """

    _providers: dict[str, type[EmailProvider]] = {
        "smtp": SMTPProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type[EmailProvider]) -> None:
        cls._providers[name] = provider_class

    @classmethod
    def create_provider(cls, provider_type: str, config: Any) -> EmailProvider:
        """
        Create a provider instance.

        Args:
            provider_type: Type of provider to create
            config: Provider configuration

        Returns:
            An instance of the requested provider

        Raises:
            ValueError: If the provider type is not supported
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Unsupported email provider type: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(config)  # type: ignore

    @classmethod
    def get_configured_provider(cls) -> EmailProvider:
        """
        Get the configured email provider.

        Returns:
            An instance of the configured email provider
        """
        provider_type = settings.EMAIL_PROVIDER_TYPE

        smtp_config = SMTPConfiguration(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_ssl=settings.SMTP_SSL,
            use_tls=settings.SMTP_TLS,
        )

        smtp_provider = MailerFactory.create_provider("smtp", smtp_config)

        if provider_type == "aws_ses":
            logger.warning("src.libs.mailer.factory.get_configured_provider:: Reverting to smtp provider")
            return smtp_provider

        return smtp_provider
