from abc import ABC, abstractmethod

from src.libs.mailer.schemas import MailerRequest, MailerResponse


class EmailProvider(ABC):
    """
    Base abstract class for all email providers.
    """

    @abstractmethod
    async def send_email(
        self,
        payload: MailerRequest,
    ) -> "MailerResponse":
        """
        Send an email.

        Args:
           payload (MailerRequest): The email body containing all relevant information

        Returns:
           MailerResponse: A response object containing information about the sent email
        """
        pass

    @abstractmethod
    async def verify_configuration(self) -> bool:
        """
        Verify that the provider is configured correctly.

        Returns:
            True if configuration is valid, False otherwise
        """
        pass
