from fastapi import status
from fastapi_problem.error import StatusProblem


class MailerError(StatusProblem):
    """Base error for mailer related issues"""

    type_ = "mailer_error"
    title = "Mailer Error"
    detail = "An error occurred in the mailer service."
    status = status.HTTP_500_INTERNAL_SERVER_ERROR


class MailerTemplateError(MailerError):
    """Raised when there is an error with email templates."""

    title = "Mailer Template Error"
    detail = "There was an error processing the email template."
    status = status.HTTP_400_BAD_REQUEST


class MailerConnectionError(MailerError):
    """Raised when there is a connection error with the mail server."""

    title = "Mailer Connection Error"
    detail = "Could not connect to the mail server."
    status = status.HTTP_503_SERVICE_UNAVAILABLE


class MailerTimeoutError(MailerError):
    """Raised when a mail sending operation times out."""

    title = "Mailer Timeout Error"
    detail = "The mail sending operation timed out."
    status = status.HTTP_400_BAD_REQUEST


class MailerInvalidRecipientError(MailerError):
    """Raised when an invalid recipient address is encountered."""

    title = "Invalid Recipient Error"
    detail = "One or more recipient email addresses are invalid."
    status = status.HTTP_400_BAD_REQUEST
