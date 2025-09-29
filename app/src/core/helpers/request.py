import re
from typing import Any, Literal

from fastapi import Request
from src.core.constants import DEFAULT_PROXY_COUNT, DEFAULT_PROXY_HEADERS
from src.core.database.mixins import FriendlyMixin
from src.core.enums import ClientPlatform, ClientType
from src.core.exceptions import errors
from src.core.types import BloomClientInfo


def is_friendly_id(value: str) -> bool:
    """
    Check if a string is a valid friendly ID.
    """
    if not value or len(value) < 2:
        return False
    prefix = value[0]
    if prefix not in ("i", "u"):
        return False
    return all(c in FriendlyMixin._ALPHABET for c in value[1:])


def parse_nested_query_params(query_params: dict[str, Any]) -> dict[str, Any]:
    """
    Parse nested query parameters like 'filters[status]' and 'include[0]' into nested dictionaries.
    """
    parsed = {}
    nested_pattern = re.compile(r"^([^[]+)\[([^]]+)\]$")

    for key, value in query_params.items():
        match = nested_pattern.match(key)
        if match:
            parent_key, child_key = match.groups()
            if parent_key not in parsed:
                parsed[parent_key] = {}
            parsed[parent_key][child_key] = value
        else:
            parsed[key] = value

    for key, value in parsed.items():
        if isinstance(value, dict) and all(k.isdigit() for k in value.keys()):
            sorted_items = sorted(value.items(), key=lambda x: int(x[0]))
            parsed[key] = [item[1] for item in sorted_items]

    return parsed


def get_client_ip(
    request: Request,
    proxy_headers: list[str] | None = None,
    trusted_proxies: list[str] | None = None,
    proxy_count: int | None = None,
) -> str | None:
    """
    Extract the client IP address using a variety of methods.
    """
    proxy_headers = proxy_headers or DEFAULT_PROXY_HEADERS
    proxy_count = proxy_count or DEFAULT_PROXY_COUNT

    for header_name in proxy_headers:
        if header_name in request.headers:
            header_value = request.headers[header_name]

            if header_name == "X-Forwarded-For" and "," in header_value:
                ips = [ip.strip() for ip in header_value.split(",")]

                if trusted_proxies:
                    if ips[-1] in trusted_proxies:
                        idx = -1 - proxy_count
                        if abs(idx) <= len(ips):
                            return ips[idx]
                else:
                    return ips[0]
            else:
                return header_value

    if hasattr(request, "client") and request.client and hasattr(request.client, "host"):
        return request.client.host

    return None


def parse_bloom_client_header(x_bloom_client: str) -> BloomClientInfo:
    """
    Parse the X-Bloom-Client header.

    Expected format: "platform=web; version=1.2.3; app=bloom-main"
    Optional build parameter: "platform=ios; version=2.1.0; app=bloom-customer; build=123"

    Args:
        x_bloom_client (str): The X-Bloom-Client header value

    Returns:
        BloomClientInfo: Parsed client information

    Raises:
        InvalidClientHeaderError: If the header format is invalid
        UnsupportedPlatformError: If the platform is not supported
        UnsupportedAppError: If the app is not supported
    """
    try:
        pairs = [pair.strip() for pair in x_bloom_client.split(";")]
        parsed_data = {}

        for pair in pairs:
            if "=" not in pair:
                raise ValueError(f"Invalid format in pair: {pair}")

            key, value = pair.split("=", 1)
            key = key.strip()
            value = value.strip()

            if not key or not value:
                raise ValueError(f"Empty key or value in pair: {pair}")

            parsed_data[key] = value

    except ValueError as e:
        raise errors.InvalidClientTypeError(detail=f"Invalid X-Bloom-Client header format: {str(e)}")

    required_fields = ["platform", "version", "app"]
    missing_fields = [field for field in required_fields if field not in parsed_data]

    if missing_fields:
        raise errors.InvalidClientTypeError(
            detail=f"Missing required fields in X-Bloom-Client header: {', '.join(missing_fields)}"
        )

    try:
        platform = ClientPlatform(parsed_data["platform"])
    except ValueError:
        valid_platforms = [p.value for p in ClientPlatform]
        raise errors.UnsupportedClientPlatformError(
            detail=f"Unsupported platform '{parsed_data['platform']}'. Supported platforms: {', '.join(valid_platforms)}"
        )

    try:
        app = ClientType(parsed_data["app"])
    except ValueError:
        valid_apps = [a.value for a in ClientType]
        raise errors.UnsupportedAppError(
            detail=f"Unsupported app '{parsed_data['app']}'. Supported apps: {', '.join(valid_apps)}"
        )

    version_pattern = re.compile(r"^\d+\.\d+\.\d+(?:[-+]\w+)?$")
    if not version_pattern.match(parsed_data["version"]):
        raise errors.InvalidClientTypeError(
            detail=f"Invalid version format '{parsed_data['version']}'. Expected format: x.y.z (e.g., 1.2.3)"
        )

    build = parsed_data.get("build")
    if build is not None and not build.isdigit():
        raise errors.InvalidClientTypeError(detail=f"Invalid build format '{build}'. Build must be numeric")

    return BloomClientInfo(platform=platform, version=parsed_data["version"], app=app, build=build)


def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "Unknown")


def get_request_info(request: Request, keys: list[Literal["user_agent", "ip_address", "request_id"]]) -> dict[str, Any]:
    """
    Extract specified information from the request object.

    Args:
        request (Request): The FastAPI request object.
        keys (list): List of keys to extract. Supported keys are 'user_agent' and 'ip_address'.

    Returns:
        dict: A dictionary containing the extracted information.
    """
    info = {}

    if "user_agent" in keys:
        user_agent = get_user_agent(request)
        info["user_agent"] = user_agent

    if "request_id" in keys:
        request_id: str | None = request.state.request_id if hasattr(request.state, "request_id") else None
        info["request_id"] = request_id or "Unknown"

    if "ip_address" in keys:
        ip_address = get_client_ip(request)
        info["ip_address"] = ip_address or "Unknown"

    return info
