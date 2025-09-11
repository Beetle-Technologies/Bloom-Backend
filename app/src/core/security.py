import hashlib
import hmac
import logging
import secrets

from src.core.config import settings

logger = logging.getLogger(__name__)


def generate_csrf(secret_key: str = settings.CSRF_SECRET_KEY) -> dict[str, str]:
    """Generate the CSRF token and signature"""

    token = secrets.token_urlsafe(32)
    signature = hmac.new(key=secret_key.encode(), msg=token.encode(), digestmod=hashlib.sha256).hexdigest()

    return {
        "token": token,
        "signature": signature,
    }


def verify_csrf_token(
    token: str,
    signature: str,
    secret_key: str = settings.CSRF_SECRET_KEY,
) -> bool:
    """Verify the CSRF token and its signature"""

    expected_signature = hmac.new(key=secret_key.encode(), msg=token.encode(), digestmod=hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
