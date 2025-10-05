import base64
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Type, TypeVar

import jwt
import pyotp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jwt import InvalidKeyError, InvalidTokenError
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from pydantic import BaseModel, ValidationError
from src.core.config import settings
from src.core.constants import SPECIAL_CHARS
from src.core.exceptions import errors
from src.core.logging import get_logger
from src.core.types import Password

if TYPE_CHECKING:
    from src.domain.schemas.auth import AuthSessionState, AuthSessionToken

logger = get_logger(__name__)

ALGORITHM = "HS256"

T = TypeVar("T")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityService:
    """Service for handling Passwords, JWT tokens and OTP generation"""

    def __init__(self):
        self.algorithm = ALGORITHM
        self.secret_key = settings.AUTH_SECRET_KEY

    def verify_password(self, *, plain_password: str, hashed_password: str, salt: str) -> bool:
        try:
            return pwd_context.verify(plain_password + salt, hashed_password)
        except UnknownHashError:
            logger.debug(
                f"{__name__}.verify_password:: Unable to verify password due to hashing error",
                exc_info=True,
            )
            return False

    def hash_password(self, *, password: str, salt_rounds: int = 32) -> tuple[str, str]:
        salt = secrets.token_hex(salt_rounds)
        pwd_hash = pwd_context.hash(password + salt)
        return pwd_hash, salt

    def create_jwt_token(
        self,
        subject: str | Any,
        expiry_time_in_secs: timedelta = timedelta(seconds=settings.AUTH_TOKEN_MAX_AGE),
    ) -> str:
        """
        Create a JWT token with the given subject and expiry time.

        Args:
            subject: The subject of the token (usually user ID or data object)
            expiry_time_in_secs: Token expiry time in seconds

        Returns:
            Encoded JWT token string
        """
        if isinstance(subject, BaseModel):
            token_subject = json.dumps(subject.model_dump())
        else:
            token_subject = subject

        expire = datetime.now(UTC) + expiry_time_in_secs
        now = datetime.now(UTC)
        payload = {
            "aud": settings.APP_NAME,
            "exp": expire,
            "iat": now,
            "nbf": now,
            "sub": token_subject,
        }
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_jwt_token(self, token: str) -> Any:
        """
        Decode and validate a JWT token.

        Args:
            token: The JWT token to decode

        Returns:
            Decoded token payload

        Raises:
            InvalidTokenError: If the token is invalid or expired
        """
        try:
            return jwt.decode(
                jwt=token,
                audience=settings.APP_NAME,
                key=self.secret_key,
                options={"require": ["exp", "iat", "nbf", "sub", "aud"]},
                algorithms=[self.algorithm],
            )
        except (InvalidTokenError, InvalidKeyError) as error:
            raise errors.InvalidTokenError() from error

    def get_token_data(self, decoded_token: dict[str, Any], target_type: Type[T]) -> T:
        """
        Parse decoded token data into a specified type.

        Args:
            decoded_token: The decoded JWT token payload
            target_type: The target type to parse the token data into (e.g., AuthSessionState)

        Returns:
            Parsed data of the specified type

        Raises:
            InvalidTokenError: If the token data cannot be parsed into the target type
        """
        try:
            subject = decoded_token.get("sub")
            if subject is None:
                raise ValueError("Token subject (sub) is missing")

            try:
                is_pydantic_model = issubclass(target_type, BaseModel)
            except TypeError:
                is_pydantic_model = False

            if is_pydantic_model:
                if isinstance(subject, str):
                    try:
                        subject_data = json.loads(subject)
                    except json.JSONDecodeError:
                        # If it's not JSON, treat it as raw data
                        subject_data = {"data": subject}
                else:
                    subject_data = subject

                return target_type(**subject_data)  # type: ignore
            else:
                # For non-Pydantic types, return the subject as-is or attempt conversion
                if isinstance(subject, target_type):
                    return subject
                else:
                    return target_type(subject)  # type: ignore

        except (ValueError, ValidationError, TypeError) as error:
            logger.error(f"Failed to parse token data into {target_type.__name__}: {error}")
            raise errors.InvalidTokenError() from error

    def generate_deterministic_password(self, src: str) -> Password:
        """
        Generate a secure deterministic password that meets the `Password` criteria from the source string.

        Args:
            length: Length of the generated password

        Returns:
            Randomly generated password string that contains at least one uppercase letter, one lowercase letter, one digit, and one special character.
        """

        seed = sum(ord(char) for char in src) + len(src)
        rng = secrets.SystemRandom(seed)

        while True:
            password_chars = [
                rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),  # At least one uppercase letter
                rng.choice("abcdefghijklmnopqrstuvwxyz"),  # At least one lowercase letter
                rng.choice("0123456789"),  # At least one digit
                rng.choice(list(SPECIAL_CHARS)),  # At least one special character
            ]

            rng.shuffle(password_chars)
            password = "".join(password_chars)

            try:
                return Password(password)
            except Exception:
                continue

    def get_cryptographic_signer(self, context: str) -> Fernet:
        """
        Get Fernet signer for encrypting/decrypting tokens.
        Note: context is used as a salt to initialize the signer.

        Ensure it is consistent & unchanged with the context it is used or else
        you won't be able to decrypt tokens later on.

        Args:
            context: Context string used as salt for key derivation

        Returns:
            Fernet instance for encryption/decryption
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=bytes(context.encode()),
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(bytes(self.secret_key.encode())))
        return Fernet(key)

    def generate_random_token(self, rounds: int = 32) -> str:
        """
        Generate a secure random token.

        Args:
            rounds: Number of rounds for token generation

        Returns:
            URL-safe random token string
        """
        return secrets.token_urlsafe(rounds)

    def generate_email_verification_token(
        self, fid: str, expiry_time: int = settings.AUTH_VERIFICATION_TOKEN_MAX_AGE
    ) -> str:
        """
        Generate a secure email verification token with expiry time

        Args:
            fid: The friendly identifier for the account

        Returns:
            URL-safe email verification token string
        """

        signer = self.get_cryptographic_signer(context="email-verification")
        encodable_data = f"{fid}__{int((datetime.now(UTC) + timedelta(seconds=expiry_time)).timestamp())}"
        token = signer.encrypt(encodable_data.encode())
        return token.decode()

    def verify_email_verification_token(
        self, token: str, expiry_time: int = settings.AUTH_VERIFICATION_TOKEN_MAX_AGE
    ) -> str:
        """
        Verify and decrypt an email verification token.

        Args:
            token: The email verification token to verify

        Returns:
            The friendly identifier (fid) if the token is valid

        Raises:
            InvalidTokenError: If the token is invalid or cannot be decrypted
        """

        signer = self.get_cryptographic_signer(context="email-verification")
        try:
            decrypted_fid = signer.decrypt(token.encode()).decode()
            fid, exp_timestamp = decrypted_fid.rsplit("__", 1)

            if int(exp_timestamp) < int(datetime.now(UTC).timestamp()):
                raise errors.InvalidVerificationLinkError("Token has expired")
            return fid
        except errors.InvalidVerificationLinkError as ite:
            raise ite
        except Exception as e:
            logger.error(f"Error decrypting email verification token: {e}")
            raise errors.InvalidVerificationLinkError() from e

    def generate_otp_secret(self) -> str:
        """
        Generate a random secret for OTP generation.

        Returns:
            Base32 encoded secret string
        """
        return pyotp.random_base32()

    def generate_totp(
        self,
        digits: int = 4,
        secret: str = settings.AUTH_OTP_SECRET_KEY,
        interval: int = settings.AUTH_OTP_MAX_AGE,
    ) -> str:
        """
        Generate a Time-based One-Time Password (TOTP).

        Args:
            secret: Base32 encoded secret key
            interval: Time interval in seconds (default: 300 seconds = 5 minutes)

        Returns:
            4-digit OTP string
        """
        totp = pyotp.TOTP(secret, digits=digits, issuer=settings.APP_NAME, interval=interval)
        return totp.now()

    def verify_totp(
        self,
        token: str,
        digits: int = 4,
        secret: str = settings.AUTH_OTP_SECRET_KEY,
        interval: int = settings.AUTH_OTP_MAX_AGE,
        window: int = 1,
    ) -> bool:
        """
        Verify a Time-based One-Time Password (TOTP).

        Args:
            token: The OTP token to verify
            secret: Base32 encoded secret key
            interval: Time interval in seconds (default: 300 seconds = 5 minutes)
            window: Number of intervals to check (default: 1, allows for clock drift)

        Returns:
            True if the token is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret, digits=digits, issuer=settings.APP_NAME, interval=interval)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            return False

    def generate_hotp(self, secret: str, counter: int) -> str:
        """
        Generate a HMAC-based One-Time Password (HOTP).

        Args:
            secret: Base32 encoded secret key
            counter: Counter value for HOTP generation

        Returns:
            6-digit OTP string
        """
        hotp = pyotp.HOTP(secret)
        return hotp.at(counter)

    def verify_hotp(self, token: str, secret: str, counter: int) -> bool:
        """
        Verify a HMAC-based One-Time Password (HOTP).

        Args:
            token: The OTP token to verify
            secret: Base32 encoded secret key
            counter: Counter value for HOTP verification

        Returns:
            True if the token is valid, False otherwise
        """
        try:
            hotp = pyotp.HOTP(secret)
            return hotp.verify(token, counter)
        except Exception as e:
            logger.error(f"Error verifying HOTP: {e}")
            return False

    def get_otp_provisioning_uri(
        self,
        secret: str,
        account_name: str,
        issuer_name: str | None = None,
        otp_type: str = "totp",
        counter: int | None = None,
        interval: int = 300,
    ) -> str:
        """
        Generate a provisioning URI for QR code generation.

        Args:
            secret: Base32 encoded secret key
            account_name: Account name (usually email or username)
            issuer_name: Name of the issuing service
            otp_type: Type of OTP ("totp" or "hotp")
            counter: Counter for HOTP (required if otp_type is "hotp")
            interval: Time interval for TOTP in seconds

        Returns:
            Provisioning URI string
        """
        if issuer_name is None:
            issuer_name = settings.APP_NAME

        if otp_type == "totp":
            totp = pyotp.TOTP(secret, interval=interval)
            return totp.provisioning_uri(name=account_name, issuer_name=issuer_name)
        elif otp_type == "hotp":
            if counter is None:
                raise ValueError("Counter is required for HOTP provisioning URI")
            hotp = pyotp.HOTP(secret)
            return hotp.provisioning_uri(name=account_name, issuer_name=issuer_name, initial_count=counter)
        else:
            raise ValueError(f"Unsupported OTP type: {otp_type}")

    def generate_auth_tokens(self, auth_session_state: "AuthSessionState") -> list["AuthSessionToken"]:
        """
        Generate access and refresh tokens for authentication.

        Args:
            auth_session_state: The authentication session state containing account info

        Returns:
            List of AuthSessionToken objects (access and refresh tokens)
        """
        from src.domain.schemas.auth import AuthSessionToken

        # Generate access token (8 hours by default)
        access_token_expiry = timedelta(seconds=settings.AUTH_TOKEN_MAX_AGE)
        access_token = self.create_jwt_token(subject=auth_session_state, expiry_time_in_secs=access_token_expiry)

        # Generate refresh token (7 days by default)
        refresh_token_expiry = timedelta(seconds=settings.AUTH_REMEMBER_TOKEN_MAX_AGE)
        refresh_token = self.create_jwt_token(subject=auth_session_state, expiry_time_in_secs=refresh_token_expiry)

        return [
            AuthSessionToken(
                scope="access",
                token=access_token,
                expires_in=settings.AUTH_TOKEN_MAX_AGE,
            ),
            AuthSessionToken(
                scope="refresh",
                token=refresh_token,
                expires_in=settings.AUTH_REMEMBER_TOKEN_MAX_AGE,
            ),
        ]


security_service = SecurityService()
