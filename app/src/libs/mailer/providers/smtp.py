import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from typing import Any

from src.core.logging import get_logger
from src.core.mjml import mjml_templates
from src.libs.mailer.exceptions import (
    MailerConnectionError,
    MailerError,
    MailerInvalidRecipientError,
    MailerTemplateError,
)
from src.libs.mailer.interface import EmailProvider
from src.libs.mailer.schemas import MailerRequest, MailerResponse, SMTPConfiguration

logger = get_logger(__name__)


class SMTPProvider(EmailProvider):
    """
    Email provider that uses SMTP.
    """

    def __init__(
        self,
        config: SMTPConfiguration,
    ) -> None:
        """
        Initialize the SMTP provider.

        Args:
            config: SMTP configuration object containing host, port, username, password, etc.
        """
        self.host = config.host
        self.port = config.port
        self.username = config.username
        self.password = config.password
        self.use_tls = config.use_tls
        self.use_ssl = config.use_ssl
        self.timeout = config.timeout or 30

    async def verify_configuration(self) -> bool:
        """
        Verify that the SMTP configuration is correct by
        attempting to connect to the SMTP server.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(host=self.host, port=self.port, timeout=self.timeout) as smtp:
                    if self.username and self.password:
                        smtp.login(self.username, self.password)
            else:
                with smtplib.SMTP(host=self.host, port=self.port, timeout=self.timeout) as smtp:
                    if self.use_tls:
                        smtp.starttls()
                    if self.username and self.password:
                        smtp.login(self.username, self.password)

            return True

        except Exception as e:
            logger.exception(f"src.libs.mailer.providers.smtp:: SMTP configuration error: {e}")
            return False

    def _create_mime_message(
        self,
        payload: MailerRequest,
    ) -> MIMEMultipart:
        """
        Create a MIME message.

        Args:
            body: The email body containing all relevant information
        Returns:
            A MIMEMultipart message
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = payload.subject
        msg["From"] = payload.sender
        msg["To"] = ", ".join(str(recipient) for recipient in payload.recipients)

        if payload.cc:
            msg["Cc"] = ", ".join(payload.cc)

        if payload.reply_to:
            msg["Reply-To"] = payload.reply_to

        if payload.message_id:
            msg["Message-ID"] = payload.message_id
        else:
            msg["Message-ID"] = make_msgid(domain=payload.sender.split("@")[1])

        if payload.text_content:
            msg.attach(MIMEText(payload.text_content, "plain", "utf-8"))

        if payload.html_content:
            msg.attach(MIMEText(payload.html_content, "html", "utf-8"))

        if payload.attachments:
            for attachment in payload.attachments:
                filename = attachment.filename
                content_type = attachment.content_type
                content = attachment.content

                part = MIMEApplication(content)
                part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                part.add_header("Content-Type", content_type)
                msg.attach(part)

        return msg

    async def send_email(
        self,
        payload: MailerRequest,
    ) -> MailerResponse:
        """
        Send an email using SMTP.

        Args:
            body: The email body containing all relevant information

        Returns:
            MailerResponse: Response object containing the result of the send operation
        """

        if not await self.verify_configuration():
            raise MailerConnectionError()

        if payload.html_content is None:

            try:
                html_content = mjml_templates.get_template(payload.template_name).render(**payload.template_context)

                payload.html_content = html_content
            except Exception as e:
                logger.exception(f"src.libs.mailer.providers.smtp:: Failed to render MJML template: {e}")
                raise MailerTemplateError()
        try:
            msg = self._create_mime_message(
                payload=payload,
            )

            all_recipients: list[str] = payload.recipients.copy()
            if payload.cc:
                all_recipients.extend(payload.cc)
            if payload.bcc:
                all_recipients.extend(payload.bcc)

            result: Any | None = None
            if self.use_ssl:
                with smtplib.SMTP_SSL(host=self.host, port=self.port, timeout=self.timeout) as smtp:
                    if self.username and self.password:
                        smtp.login(self.username, self.password)

                    result = smtp.send_message(msg, from_addr=payload.sender, to_addrs=all_recipients)
            else:
                with smtplib.SMTP(host=self.host, port=self.port, timeout=self.timeout) as smtp:
                    if self.use_tls:
                        smtp.starttls()

                    if self.username and self.password:
                        smtp.login(self.username, self.password)

                    result = smtp.send_message(msg, from_addr=payload.sender, to_addrs=all_recipients)

            return MailerResponse(
                provider="smtp",
                message_id=msg["Message-ID"],
                status="sent",
                raw_response={"message": "Email sent successfully", "smtp_response": result},
            )
        except smtplib.SMTPRecipientsRefused as e:
            logger.exception(f"src.libs.mailer.providers.smtp:: SMTP recipients refused: {e.recipients}")
            raise MailerInvalidRecipientError()
        except smtplib.SMTPAuthenticationError as e:
            logger.exception(f"src.libs.mailer.providers.smtp:: SMTP authentication error: {e}")
            raise MailerConnectionError(
                message="SMTP authentication failed",
                provider="smtp",
                status="error",
            )
        except Exception as e:
            logger.exception(f"src.lib.emailer.providers.smtp:: Failed to send email via SMTP: {e}")
            raise MailerError(detail="Failed to send email via SMTP")
