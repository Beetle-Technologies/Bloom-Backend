import base64
import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jwt import InvalidKeyError, InvalidTokenError
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from src.core.config import settings
from src.core.exceptions import errors

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def create_access_token(
    subject: str | Any,
    expiry_time_in_secs: timedelta = timedelta(seconds=settings.AUTH_TOKEN_MAX_AGE),
) -> str:
    expire = datetime.now(UTC) + expiry_time_in_secs
    now = datetime.now(UTC)
    payload = {
        "exp": expire,
        "iat": now,
        "nbf": now,
        "sub": str(subject),
    }
    encoded_jwt = jwt.encode(payload, settings.AUTH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Any:
    try:
        return jwt.decode(
            jwt=token,
            key=settings.AUTH_SECRET_KEY,
            options={"require": ["exp", "iat", "nbf", "sub"]},
            algorithms=[ALGORITHM],
        )
    except (InvalidTokenError, InvalidKeyError) as error:
        raise errors.InvalidTokenError() from error


def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    try:
        return pwd_context.verify(plain_password + salt, hashed_password)
    except UnknownHashError:
        logger.debug(
            f"{__name__}.verify_password:: Unable to verify password due to hashing error",
            exc_info=True,
        )
        return False


def hash_password(password: str, salt_rounds: int = 32) -> tuple[str, str]:
    salt = secrets.token_hex(salt_rounds)
    pwd_hash = pwd_context.hash(password + salt)
    return pwd_hash, salt


def get_cryptographic_signer(context: str) -> Fernet:
    """
    Get ferenet signer.
    Note context is used as a salt to initialize the signer.

    Ensure it is consistent & unchanged with the context it is used or else.
    You wont be able to decrypt tokens later on.
    """

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=bytes(context.encode()),
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(bytes(settings.AUTH_SECRET_KEY.encode())))
    return Fernet(key)


def generate_random_token(rounds: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(rounds)


def generate_csrf(secret_key: str = settings.CSRF_SECRET_KEY) -> dict[str, str]:
    """Generate the CSRF token and signature"""

    token = secrets.token_urlsafe(32)
    signature = hmac.new(
        key=secret_key.encode(), msg=token.encode(), digestmod=hashlib.sha256
    ).hexdigest()

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

    expected_signature = hmac.new(
        key=secret_key.encode(), msg=token.encode(), digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
