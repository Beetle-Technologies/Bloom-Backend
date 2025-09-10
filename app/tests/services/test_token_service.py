import uuid
from datetime import timedelta
from unittest.mock import patch

import pyotp
import pytest
from src.core.exceptions import errors
from src.core.types import GUID
from src.domain.enums import AccountTypeEnum
from src.domain.schemas import AuthSessionState

from app.src.domain.services.security_service import SecurityService, security_service


class TestTokenService:
    """Test cases for TokenService"""

    def setup_method(self):
        """Setup method to create a fresh TokenService instance for each test."""
        self.token_service = SecurityService()

    def test_token_service_singleton(self):
        """Test that the global token_service instance works correctly."""
        assert security_service is not None
        assert isinstance(security_service, SecurityService)

    def test_create_jwt_token(self):
        """Test JWT token creation."""
        subject = "user123"
        token = self.token_service.create_jwt_token(subject)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        parts = token.split(".")
        assert len(parts) == 3

    def test_create_jwt_token_with_custom_expiry(self):
        """Test JWT token creation with custom expiry time."""
        subject = "user123"
        custom_expiry = timedelta(minutes=30)
        token = self.token_service.create_jwt_token(subject=subject, expiry_time_in_secs=custom_expiry)

        assert token is not None
        payload = self.token_service.decode_jwt_token(token)
        assert payload["sub"] == str(subject)

    def test_decode_valid_token(self):
        """Test decoding a valid JWT token."""
        subject = "user123"
        token = self.token_service.create_jwt_token(subject)

        payload = self.token_service.decode_jwt_token(token)

        assert payload["sub"] == str(subject)
        assert "exp" in payload
        assert "iat" in payload
        assert "nbf" in payload

    def test_decode_invalid_token(self):
        """Test decoding an invalid JWT token raises appropriate error."""
        invalid_token = "invalid.jwt.token"

        with pytest.raises(errors.InvalidTokenError):
            self.token_service.decode_jwt_token(invalid_token)

    def test_decode_malformed_token(self):
        """Test decoding a malformed token."""
        malformed_token = "not-a-jwt"

        with pytest.raises(errors.InvalidTokenError):
            self.token_service.decode_jwt_token(malformed_token)

    def test_generate_otp_secret(self):
        """Test OTP secret generation."""
        secret = self.token_service.generate_otp_secret()

        assert secret is not None
        assert isinstance(secret, str)
        assert len(secret) == 32  # pyotp.random_base32() generates 32-char strings

        try:
            pyotp.TOTP(secret)
        except Exception:
            pytest.fail("Generated secret is not valid base32")

    def test_generate_totp(self):
        """Test TOTP generation."""
        secret = self.token_service.generate_otp_secret()
        totp_code = self.token_service.generate_totp(secret)

        assert totp_code is not None
        assert isinstance(totp_code, str)
        assert len(totp_code) == 6
        assert totp_code.isdigit()

    def test_verify_totp_valid(self):
        """Test TOTP verification with valid code."""
        secret = self.token_service.generate_otp_secret()
        totp_code = self.token_service.generate_totp(secret)

        is_valid = self.token_service.verify_totp(totp_code, secret)
        assert is_valid is True

    def test_verify_totp_invalid(self):
        """Test TOTP verification with invalid code."""
        secret = self.token_service.generate_otp_secret()
        invalid_code = "000000"

        is_valid = self.token_service.verify_totp(invalid_code, secret)
        assert is_valid is False

    def test_generate_hotp(self):
        """Test HOTP generation."""
        secret = self.token_service.generate_otp_secret()
        counter = 1
        hotp_code = self.token_service.generate_hotp(secret, counter)

        assert hotp_code is not None
        assert isinstance(hotp_code, str)
        assert len(hotp_code) == 6
        assert hotp_code.isdigit()

    def test_verify_hotp_valid(self):
        """Test HOTP verification with valid code."""
        secret = self.token_service.generate_otp_secret()
        counter = 1
        hotp_code = self.token_service.generate_hotp(secret, counter)

        is_valid = self.token_service.verify_hotp(hotp_code, secret, counter)
        assert is_valid is True

    def test_verify_hotp_invalid(self):
        """Test HOTP verification with invalid code."""
        secret = self.token_service.generate_otp_secret()
        counter = 1
        invalid_code = "000000"

        is_valid = self.token_service.verify_hotp(invalid_code, secret, counter)
        assert is_valid is False

    def test_get_totp_provisioning_uri(self):
        """Test TOTP provisioning URI generation."""
        secret = self.token_service.generate_otp_secret()
        account_name = "test@example.com"
        issuer_name = "Test App"

        uri = self.token_service.get_otp_provisioning_uri(
            secret=secret,
            account_name=account_name,
            issuer_name=issuer_name,
            otp_type="totp",
        )

        assert uri is not None
        assert isinstance(uri, str)
        assert uri.startswith("otpauth://totp/")
        assert account_name in uri
        assert issuer_name in uri
        assert secret in uri

    def test_get_hotp_provisioning_uri(self):
        """Test HOTP provisioning URI generation."""
        secret = self.token_service.generate_otp_secret()
        account_name = "test@example.com"
        issuer_name = "Test App"
        counter = 0

        uri = self.token_service.get_otp_provisioning_uri(
            secret=secret,
            account_name=account_name,
            issuer_name=issuer_name,
            otp_type="hotp",
            counter=counter,
        )

        assert uri is not None
        assert isinstance(uri, str)
        assert uri.startswith("otpauth://hotp/")
        assert account_name in uri
        assert issuer_name in uri
        assert secret in uri

    def test_get_hotp_provisioning_uri_without_counter_raises_error(self):
        """Test HOTP provisioning URI generation without counter raises error."""
        secret = self.token_service.generate_otp_secret()
        account_name = "test@example.com"

        with pytest.raises(ValueError, match="Counter is required for HOTP"):
            self.token_service.get_otp_provisioning_uri(secret=secret, account_name=account_name, otp_type="hotp")

    def test_unsupported_otp_type_raises_error(self):
        """Test unsupported OTP type raises error."""
        secret = self.token_service.generate_otp_secret()
        account_name = "test@example.com"

        with pytest.raises(ValueError, match="Unsupported OTP type"):
            self.token_service.get_otp_provisioning_uri(secret=secret, account_name=account_name, otp_type="invalid")

    def test_get_cryptographic_signer(self):
        """Test cryptographic signer creation."""
        context = "test_context"
        signer = self.token_service.get_cryptographic_signer(context)

        assert signer is not None

        # Test encryption/decryption
        test_data = "sensitive information"
        encrypted = signer.encrypt(test_data.encode())
        decrypted = signer.decrypt(encrypted).decode()

        assert decrypted == test_data

    def test_cryptographic_signer_context_consistency(self):
        """Test that same context produces same signer."""
        context = "test_context"
        signer1 = self.token_service.get_cryptographic_signer(context)
        signer2 = self.token_service.get_cryptographic_signer(context)

        # Test that both signers can decrypt each other's data
        test_data = "test message"
        encrypted_by_1 = signer1.encrypt(test_data.encode())
        decrypted_by_2 = signer2.decrypt(encrypted_by_1).decode()

        assert decrypted_by_2 == test_data

    def test_generate_random_token_default(self):
        """Test random token generation with default rounds."""
        token = self.token_service.generate_random_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_random_token_custom_rounds(self):
        """Test random token generation with custom rounds."""
        rounds = 16
        token = self.token_service.generate_random_token(rounds=rounds)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_multiple_tokens_are_different(self):
        """Test that multiple generated tokens are different."""
        token1 = self.token_service.generate_random_token()
        token2 = self.token_service.generate_random_token()

        assert token1 != token2

    @patch("src.domain.services.token_service.logger")
    def test_verify_totp_with_exception_logs_error(self, mock_logger):
        """Test that TOTP verification logs errors when exceptions occur."""
        # Use invalid secret to trigger an exception
        invalid_secret = "invalid"
        token = "123456"

        result = self.token_service.verify_totp(token, invalid_secret)

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("src.domain.services.token_service.logger")
    def test_verify_hotp_with_exception_logs_error(self, mock_logger):
        """Test that HOTP verification logs errors when exceptions occur."""
        # Use invalid secret to trigger an exception
        invalid_secret = "invalid"
        token = "123456"
        counter = 1

        result = self.token_service.verify_hotp(token, invalid_secret, counter)

        assert result is False
        mock_logger.error.assert_called_once()

    def test_get_token_data_with_pydantic_model(self):
        """Test get_token_data with a Pydantic model."""
        # Create a test AuthSessionState
        session_state = AuthSessionState(
            id=GUID(str(uuid.uuid4())),
            type_info_id=GUID(str(uuid.uuid4())),
            type=AccountTypeEnum.USER,
        )

        # Create token with the session state
        token = self.token_service.create_jwt_token(session_state)

        # Decode token
        decoded_token = self.token_service.decode_jwt_token(token)

        # Parse token data back into AuthSessionState
        parsed_session_state = self.token_service.get_token_data(decoded_token, AuthSessionState)

        # Verify the parsed data matches the original
        assert isinstance(parsed_session_state, AuthSessionState)
        assert parsed_session_state.id == session_state.id
        assert parsed_session_state.type_info_id == session_state.type_info_id
        assert parsed_session_state.type == session_state.type

    def test_get_token_data_with_string_type(self):
        """Test get_token_data with a simple string type."""
        subject = "user123"

        # Create token with string subject
        token = self.token_service.create_jwt_token(subject)

        # Decode token
        decoded_token = self.token_service.decode_jwt_token(token)

        # Parse token data back to string
        parsed_subject = self.token_service.get_token_data(decoded_token, str)

        # Verify the parsed data matches the original
        assert isinstance(parsed_subject, str)
        assert parsed_subject == subject

    def test_get_token_data_with_missing_subject(self):
        """Test get_token_data with missing subject raises error."""
        # Create a fake decoded token without 'sub'
        decoded_token = {"exp": 1234567890, "iat": 1234567800}

        with pytest.raises(errors.InvalidTokenError):
            self.token_service.get_token_data(decoded_token, str)

    def test_get_token_data_with_validation_error(self):
        """Test get_token_data with Pydantic validation error."""
        # Create a decoded token with invalid data for AuthSessionState
        decoded_token = {
            "sub": '{"invalid_field": "value"}',
            "exp": 1234567890,
            "iat": 1234567800,
        }

        with pytest.raises(errors.InvalidTokenError):
            self.token_service.get_token_data(decoded_token, AuthSessionState)


class TestTokenServiceIntegration:
    """Integration tests for TokenService"""

    def test_complete_otp_workflow(self):
        """Test complete OTP workflow from secret generation to verification."""
        # Generate secret
        secret = security_service.generate_otp_secret()

        # Generate provisioning URI
        uri = security_service.get_otp_provisioning_uri(
            secret=secret,
            account_name="integration@test.com",
            issuer_name="Integration Test",
        )

        # Generate TOTP
        totp_code = security_service.generate_totp(secret)

        # Verify TOTP
        is_valid = security_service.verify_totp(totp_code, secret)

        assert is_valid is True
        assert "integration@test.com" in uri

    def test_complete_jwt_workflow(self):
        """Test complete JWT workflow from creation to verification."""
        user_id = "integration_user_123"

        # Create token
        token = security_service.create_jwt_token(user_id)

        # Decode token
        payload = security_service.decode_jwt_token(token)

        # Verify payload
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload

    def test_encryption_workflow(self):
        """Test complete encryption workflow."""
        context = "integration_test_context"
        sensitive_data = "This is highly sensitive user data!"

        # Get signer
        signer = security_service.get_cryptographic_signer(context)

        # Encrypt
        encrypted = signer.encrypt(sensitive_data.encode())

        # Decrypt with same context
        signer2 = security_service.get_cryptographic_signer(context)
        decrypted = signer2.decrypt(encrypted).decode()

        assert decrypted == sensitive_data
