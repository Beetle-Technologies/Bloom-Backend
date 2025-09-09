from src.libs.mailer.factory import MailerFactory
from src.libs.mailer.schemas import MailerRequest, MailerResponse

provider = MailerFactory.get_configured_provider()


class MailerService:

    async def send_email(
        self,
        payload: MailerRequest,
    ) -> MailerResponse:
        """
        Send an email using the configured email provider.

        Args:
            payload (MailerRequest): MailerRequest object containing email details

        Returns:
            MailerResponse: object with the result of the email sending operation

        Raises:
            MailerError: if sending the email fails
        """

        return await provider.send_email(payload=payload)


mailer_service = MailerService()
