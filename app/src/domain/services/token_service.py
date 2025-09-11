from __future__ import annotations

import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.exceptions import errors
from src.domain.models import Token
from src.domain.repositories import TokenRepository
from src.domain.schemas import TokenCreate

logger = logging.getLogger(__name__)


class TokenService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.token_repository = TokenRepository(session=self.session)

    async def create_token(self, *, token: str) -> Token:
        """
        Create a new token.

        Args:
            token (str): The token string

        Returns:
            Token: The created token

        Raises:
            ServiceError: If there is an error creating the token
        """
        try:
            schema = TokenCreate(token=token)
            return await self.token_repository.create_if_not_exists(schema)

        except errors.DatabaseError as de:
            logger.error(f"DatabaseError creating token: {de.detail}", exc_info=True)
            raise errors.ServiceError(detail="Failed to create token", status=500) from de
        except Exception as e:
            logger.error(f"Unexpected error creating token: {str(e)}", exc_info=True)
            raise errors.ServiceError(detail="Failed to create token", status=500) from e

    async def get_token(self, *, token: str) -> Token | None:
        """
        Get a token by its token string.

        Args:
            token (str): The token string

        Returns:
            Token | None: The token if found, otherwise None
        """
        try:
            return await self.token_repository.find_by_token(token)
        except Exception as e:
            logger.error(f"Error getting token: {str(e)}", exc_info=True)
            return None

    async def revoke_token(self, *, token: str) -> bool:
        """
        Revoke a token.

        Args:
            token (str): The token string to revoke

        Returns:
            bool: True if token was revoked, False if not found

        Raises:
            ServiceError: If there is an error revoking the token
        """
        try:
            return await self.token_repository.revoke_token(token)

        except errors.DatabaseError as de:
            logger.error(f"DatabaseError revoking token: {de.detail}", exc_info=True)
            raise errors.ServiceError(detail="Failed to revoke token", status=500) from de
        except Exception as e:
            logger.error(f"Unexpected error revoking token: {str(e)}", exc_info=True)
            raise errors.ServiceError(detail="Failed to revoke token", status=500) from e

    async def is_token_valid(self, *, token: str) -> bool:
        """
        Check if a token is valid (exists, not revoked, not deleted).

        Args:
            token (str): The token string

        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            token_obj = await self.get_token(token=token)

            if not token_obj:
                return False

            # Check if token is revoked or deleted
            return not token_obj.revoked and token_obj.deleted_datetime is None

        except Exception as e:
            logger.error(f"Error checking token validity: {str(e)}", exc_info=True)
            return False

    async def get_active_tokens(self) -> list[Token]:
        """
        Get all active tokens.

        Returns:
            list[Token]: List of active tokens
        """
        try:
            return await self.token_repository.find_active_tokens()
        except Exception as e:
            logger.error(f"Error getting active tokens: {str(e)}", exc_info=True)
            return []
