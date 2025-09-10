from __future__ import annotations

import logging

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.domain.models.permission import Permission
from src.domain.repositories.base_repository import BaseRepository
from src.domain.schemas import PermissionCreate, PermissionUpdate

logger = logging.getLogger(__name__)


class PermissionRepository(BaseRepository[Permission, PermissionCreate, PermissionUpdate]):
    """
    Repository for managing permissions in the system.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Permission, session)

    async def find_by_scope(self, scope: str) -> Permission | None:
        """
        Find a permission by its scope (resource:action).

        Args:
            scope (str): The permission scope to search for

        Returns:
            Permission | None: The found permission or None
        """
        if ":" not in scope:
            return None

        resource, action = scope.split(":", 1)
        return await self.find_one_by_and_none(resource=resource, action=action)

    async def find_by_resource(self, resource: str) -> list[Permission]:
        """
        Find all permissions for a specific resource.

        Args:
            resource (str): The resource to search for

        Returns:
            list[Permission]: List of permissions for the resource
        """
        query = select(self.model).where(self.model.resource == resource)
        result = await self.session.exec(query)
        return list(result.all())

    async def find_by_action(self, action: str) -> list[Permission]:
        """
        Find all permissions for a specific action.

        Args:
            action (str): The action to search for

        Returns:
            list[Permission]: List of permissions for the action
        """
        query = select(self.model).where(self.model.action == action)
        result = await self.session.exec(query)
        return list(result.all())

    async def create_if_not_exists(self, schema: PermissionCreate) -> Permission:
        """
        Create a permission if it doesn't already exist.

        Args:
            schema (PermissionCreate): The permission data

        Returns:
            Permission: The existing or newly created permission
        """
        existing = await self.find_one_by_and_none(resource=schema.resource, action=schema.action)

        if existing:
            return existing

        return await self.create(schema)

    async def bulk_create_if_not_exists(self, schemas: list[PermissionCreate]) -> list[Permission]:
        """
        Create multiple permissions if they don't already exist.

        Args:
            schemas (list[PermissionCreate]): List of permission data

        Returns:
            list[Permission]: List of existing or newly created permissions
        """
        permissions = []
        for schema in schemas:
            permission = await self.create_if_not_exists(schema)
            permissions.append(permission)

        return permissions
