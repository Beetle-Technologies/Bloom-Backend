from fastapi import status

from .base import ServiceError


class AccountNotFoundError(ServiceError):
    """
    This error is raised when an account is not found in the system.
    """

    title = "Account Not Found"
    detail = "The requested account does not exist"
    status = status.HTTP_404_NOT_FOUND


class AccountAlreadyExistsError(ServiceError):
    """
    This error is raised when an attempt is made to create an account that already exists.
    """

    title = "Account Already Exists"
    detail = "An account with the provided details already exists"
    status = status.HTTP_409_CONFLICT


class AccountCreationError(ServiceError):
    """
    This error is raised when there is an issue during account creation.
    """

    title = "Account Registration Failed"
    detail = "An error occurred while trying to register an account"
    status = status.HTTP_500_INTERNAL_SERVER_ERROR


class AccountUnverifiedError(ServiceError):
    """
    This error is raised when an account is not verified.
    """

    title = "Account Not Verified"
    detail = "This account has not been verified"
    status = status.HTTP_403_FORBIDDEN


class AccountUpdateError(ServiceError):
    """
    This error is raised when there is an issue updating an account.
    """

    title = "Account Update Failed"
    detail = "An error occurred while trying to update the account"
    status = status.HTTP_500_INTERNAL_SERVER_ERROR


class AccountVerificationError(ServiceError):
    """
    This error is raised raised when verification of an account fails
    """

    title = "Account Verification Failed"
    detail = "An error occurred while verifying your account"


class AccountPreCheckError(ServiceError):
    """
    This error is raised when the pre-checks for an account fail.
    """

    title = "Account Pre-Check Failed"
    detail = "An error occurred during the account pre-check process."


class AccountConfirmationError(ServiceError):
    """
    This error is raised when the confirmation of an account fails
    """

    title = "Account Confirmation Failed"
    detail = "An error occured when trying to confirm a detail on your account"


class AccountSuspendedError(ServiceError):
    """
    This error is raised when an account is suspended and cannot be used.
    """

    title = "Account Suspended"
    detail = "This account is currently suspended and cannot be accessed."
    status = status.HTTP_403_FORBIDDEN


class AccountLockedError(ServiceError):
    """
    This error is raised when an account is locked due to multiple failed login attempts.
    """

    title = "Account Locked"
    detail = "This account has been locked due to multiple failed login attempts."
    status = status.HTTP_403_FORBIDDEN


class AccountChangePasswordMismatchError(ServiceError):
    """
    This error is raised when there is a mismatch in the provided password.
    """

    title = "Password Change Mismatch"
    detail = "The provided password matches the current password."


class AccountInvalidPasswordError(ServiceError):
    """
    This error is raised when an invalid password is provided for an account.
    """

    title = "Invalid Password"
    detail = "The provided password is incorrect"
    status = status.HTTP_403_FORBIDDEN


class AccountIneligibleError(ServiceError):
    """
    This error is raised when an account is not eligible to perform a specific action.
    """

    title = "Account Not Eligible"
    detail = "This account is not eligible to perform this action"
    status = status.HTTP_403_FORBIDDEN
