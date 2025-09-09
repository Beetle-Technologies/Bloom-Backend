from enum import StrEnum


class Platform(StrEnum):
    """
    Enumeration of supported platforms.

    Attributes:
        WEB: Represents web platform.
        IOS: Represents iOS platform.
        ANDROID: Represents Android platform.
    """

    WEB = "web"
    IOS = "ios"
    ANDROID = "android"


class AppName(StrEnum):
    """
    Enumeration of supported application names.

    Attributes:
        BLOOM_MAIN: Represents the main Bloom application.
        BLOOM_SUPPLIER: Represents the Bloom supplier application.
        BLOOM_BUSINESS: Represents the Bloom business application.
        BLOOM_ADMIN: Represents the Bloom admin application.
    """

    BLOOM_MAIN = "bloom-main"
    BLOOM_SUPPLIER = "bloom-supplier"
    BLOOM_BUSINESS = "bloom-business"
    BLOOM_ADMIN = "bloom-admin"
