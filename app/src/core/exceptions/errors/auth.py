from fastapi import status

from .base import ServiceError


class AuthenticationError(ServiceError):
    """
    An base error indicating that authentication credentials were not provided, invalid or expired.
    """

    title = "Invalid credentials"
    detail = "Please provide valid authentication credentials."


class InvalidTokenError(AuthenticationError):
    """
    An error indicating that the provided authentication token is invalid or expired.
    """

    title = "Invalid or expired authentication token"
    detail = "Please login to continue."
    status = status.HTTP_401_UNAUTHORIZED


class InvalidPasswordResetTokenError(AuthenticationError):
    """
    An error indicating that the provided password reset token is invalid or expired.
    """

    title = "Invalid or expired password reset token"
    detail = "The password reset token is invalid or has expired. Please request a new password reset."
    status = status.HTTP_400_BAD_REQUEST


class InvalidOTPError(AuthenticationError):
    """
    An error indicating that the provided OTP is invalid or expired.
    """

    title = "Invalid or expired OTP"
    detail = "The OTP is invalid or has expired. Please request a new OTP."
    status = status.HTTP_400_BAD_REQUEST


class InvalidVerificationLinkError(AuthenticationError):
    """
    An error indicating that the provided verification link is invalid or expired.
    """

    title = "Invalid or expired verification link"
    detail = "The verification link is invalid or has expired. Please request a new verification email."
    status = status.HTTP_400_BAD_REQUEST
