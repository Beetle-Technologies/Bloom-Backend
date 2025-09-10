from enum import StrEnum


class TokenVerificationRequestTypeEnum(StrEnum):
    """
    Enumeration for different types of token requests.

    Attributes:
        STATE_KEY (str): Represents a state key token request that will be in the url on the client
        OTP (str): Represents a one-time password token request.
    """

    STATE_KEY = "state_key"
    OTP = "otp"


class AuthPreCheckTypeEnum(StrEnum):
    """
    Enumeration for different types of pre-check requests.

    Attributes:
        EMAIL (str): Represents a pre-check request for an email address.
        USERNAME (str): Represents a pre-check request for a username.
    """

    EMAIL = "email"
    USERNAME = "username"
