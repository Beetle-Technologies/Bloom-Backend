from typing import Any

from pydantic import BaseModel, EmailStr, PositiveInt


class AWSSESConfiguration(BaseModel):
    """
    Schema for AWS SES email provider.

    Attributes:
        aws_access_key_id (str): AWS access key ID.
        aws_secret_access_key (str): AWS secret access key.
        region_name (str): AWS region name.
    """

    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str


class SMTPConfiguration(BaseModel):
    """
    Schema for SMTP email provider.

    Attributes:
        host (str): SMTP server host.
        port (PositiveInt): SMTP server port.
        username (str | None): SMTP username.
        password (str | None): SMTP password.
        use_tls (bool): Whether to use TLS.
        use_ssl (bool): Whether to use SSL.
        timeout (PositiveInt): Connection timeout in seconds.
    """

    host: str
    port: PositiveInt
    username: str | None
    password: str | None
    use_tls: bool
    use_ssl: bool
    timeout: PositiveInt = 30


class EmailAttachment(BaseModel):
    """
    Schema for email attachments.

    Attributes:
        filename (str): Name of the attachment file.
        content (bytes): Content of the attachment file.
        content_type (str): MIME type of the attachment file.
    """

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


class MailerRequest(BaseModel):
    """
    Schema for email sending requests.

    Attributes:
        template_name (str): Name of the email template to use.
        template_context (dict[str, Any]): Context variables for rendering the template.
        sender (EmailStr): Email address of the sender.
        recipients (list[EmailStr]): List of recipient email addresses.
        subject (str): Subject of the email.
        html_content (str | None): HTML content of the email.
        text_content (str | None): Plain text content of the email.
        cc (list[EmailStr] | None): List of CC email addresses.
        bcc (list[EmailStr] | None): List of BCC email addresses.
        reply_to (EmailStr | None): Reply-To email address.
        attachments (list[EmailAttachment] | None): List of email attachments.
        message_id (str | None): Custom message ID for the email.
    """

    template_name: str
    template_context: dict[str, Any] = {}
    sender: EmailStr
    recipients: list[EmailStr]
    subject: str
    html_content: str | None = None
    text_content: str | None = None
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None
    reply_to: EmailStr | None = None
    attachments: list[EmailAttachment] | None = None
    message_id: str | None = None

    class Config:
        arbitrary_types_allowed = True


class MailerResponse(BaseModel):
    """
    Schema for email sending responses.

    Attributes:
        provider (str): Name of the email provider used.
        message_id (str | None): Message ID returned by the email provider.
        status (str): Status of the email sending operation (e.g., "sent", "failed").
        error_code (str | None): Error code if the email sending failed.
        error_message (str | None): Error message if the email sending failed.
        raw_response (dict[str, Any] | None): Raw response from the email provider.
    """

    provider: str
    message_id: str | None = None
    status: str
    error_code: str | None = None
    error_message: str | None = None
    raw_response: dict[str, Any] | None = None
