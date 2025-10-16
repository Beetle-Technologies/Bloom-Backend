from contextvars import ContextVar

SPECIAL_CHARS: set[str] = {
    "!",
    "@",
    "#",
    "$",
    "%",
    "^",
    "&",
    "*",
    "(",
    ")",
    "-",
    "_",
    "=",
    "+",
    "{",
    "}",
    "[",
    "]",
    "|",
    "\\",
    ":",
    ";",
    "'",
    '"',
    "<",
    ">",
    ",",
    ".",
    "?",
    "/",
}


REQUEST_ID_CTX = ContextVar("request_id", default="")

DEFAULT_PAGE_SIZE = 20

# Proxy headers for client IP detection
DEFAULT_PROXY_HEADERS = [
    "X-Forwarded-For",
    "X-Real-IP",
    "CF-Connecting-IP",
    "True-Client-IP",
    "X-Client-IP",
    "Fastly-Client-IP",
    "X-Azure-ClientIP",
]

DEFAULT_PROXY_COUNT = 1

BLOOM_CLIENT_HEADER = "X-Bloom-Client"

ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
]

DEFAULT_CATALOG_RETURN_FIELDS = [
    "id",
    "friendly_id",
    "name",
    "description",
    "price",
    "status",
    "attributes",
    "is_digital",
    "created_datetime",
    "updated_datetime",
]


CURRENCY_SYMBOL_MAP: dict[str, str] = {
    "US Dollar": "$",
    "Euro": "€",
    "Pound Sterling": "£",
    "Yen": "¥",
    "Canadian Dollar": "CA$",
    "Australian Dollar": "A$",
    "Swiss Franc": "CHF",
    "Yuan Renminbi": "¥",
    "Indian Rupee": "₹",
    "Brazilian Real": "R$",
    "Naira": "₦",
    "Rand": "R",
    "Kenyan Shilling": "KSh",
    "Ghana Cedi": "GH₵",
    "Egyptian Pound": "E£",
}

CURRENCY_ISO_CODE_MAP: dict[str, str] = {
    "US Dollar": "USD",
    "Euro": "EUR",
    "Pound Sterling": "GBP",
    "Yen": "JPY",
    "Canadian Dollar": "CAD",
    "Australian Dollar": "AUD",
    "Swiss Franc": "CHF",
    "Yuan Renminbi": "CNY",
    "Indian Rupee": "INR",
    "Brazilian Real": "BRL",
    "Naira": "NGN",
    "Rand": "ZAR",
    "Kenyan Shilling": "KES",
    "Ghana Cedi": "GHS",
    "Egyptian Pound": "EGP",
}


def get_currency_symbol(code: str) -> str:
    """Get currency symbol from currency code"""
    return CURRENCY_SYMBOL_MAP.get(code, code)


def get_currency_iso_code(code: str) -> str:
    """Get ISO currency code from currency name"""
    return CURRENCY_ISO_CODE_MAP.get(code, "")


def format_currency(amount: float, currency_code: str) -> str:
    """Format amount with currency symbol"""
    symbol = get_currency_symbol(currency_code)
    return f"{symbol}{amount:,.2f}"
