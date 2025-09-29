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
