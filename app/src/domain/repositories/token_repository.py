from __future__ import annotations

import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from src.domain.models.token import Token
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import TokenCreate, TokenUpdate
from src.libs.query_engine import GeneralPaginationRequest

logger = logging.getLogger(__name__)


class TokenRepository(BaseRepository[Token, TokenCreate, TokenUpdate]):
    """
    Repository for managing tokens in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Token, session)

    async def find_by_token(self, token: str) -> Token | None:
        """
        Find a token by its token string.

        Args:
            token (str): The token string

        Returns:
            Token | None: The token if found, otherwise None
        """
        return await self.find_one_by_and_none(token=token)

    async def find_active_tokens(self) -> list[Token]:
        """
        Find all active (non-revoked, non-deleted) tokens.

        Returns:
            list[Token]: List of active tokens
        """

        pagination = GeneralPaginationRequest(filters={"revoked__eq": False, "deleted_datetime__is_null": True})

        response = await self.find(pagination=pagination)
        return response.items

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by setting its revoked flag to True.

        Args:
            token (str): The token string to revoke

        Returns:
            bool: True if token was revoked, False if not found
        """
        token_obj = await self.find_by_token(token)
        if not token_obj:
            return False

        updated = await self.update(token_obj.id, {"revoked": True})
        return updated is not None

    async def create_if_not_exists(self, schema: TokenCreate) -> Token:
        """
        Create a token if it doesn't already exist.

        Args:
            schema (TokenCreate): The token data

        Returns:
            Token: The existing or newly created token
        """
        existing = await self.find_by_token(schema.token)

        if existing:
            return existing

        return await self.create(schema)

    async def bulk_create_if_not_exists(self, tokens: list[TokenCreate]) -> list[Token]:
        """
        Create multiple tokens if they do not already exist.

        Args:
            tokens (list[TokenCreate]): The list of token schemas to create

        Returns:
            list[Token]: The list of created tokens
        """
        results = []
        for schema in tokens:
            token = await self.create_if_not_exists(schema)
            results.append(token)
        return results
