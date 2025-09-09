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


# Bloom client header constant
BLOOM_CLIENT_HEADER = "X-Bloom-Client"
