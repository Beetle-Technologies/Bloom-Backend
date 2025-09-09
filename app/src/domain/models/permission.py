from typing import ClassVar

from sqlalchemy import ColumnElement, String, UniqueConstraint, func, type_coerce
from sqlalchemy.ext.hybrid import hybrid_property
from sqlmodel import Field
from src.core.database.mixins import CreatedDateTimeMixin, IntegerIDMixin


class Permission(IntegerIDMixin, CreatedDateTimeMixin, table=True):
    """
    Represents a permission in the system.

    Attributes:\n
        id (int): Unique identifier for the permission.
        resource (str): The resource of the permission i.e the table name (e.g users, projects).
        action (str): The action associated with the permission (e.g create, read).
        description (str): A brief description of the permission.
        scope (str): The full permission scope in the format 'resource:action'.
        created_datetime (datetime): The timestamp when the permission was created.
    """

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )

    SELECTABLE_FIELDS = [
        "id",
        "resource",
        "action",
        "description",
        "scope",
        "created_datetime",
    ]

    resource: str = Field(nullable=False, index=True)
    action: str = Field(nullable=False, index=True)
    description: str | None = Field(default=None)

    # Properties
    scope: ClassVar = hybrid_property(lambda self: f"{self.resource}:{self.action}")

    @scope.inplace.setter
    def _scope_setter(self, value: str):
        """
        Set the permission scope from a string in the format 'resource:action'.
        """
        if ":" not in value:
            raise ValueError("Scope must be in the format 'resource:action'")
        self.resource, self.action = value.split(":", 1)

    @scope.inplace.expression
    def _scope_expression(cls) -> ColumnElement[str]:
        """
        SQL expression for the scope property.
        """
        return type_coerce(func.concat(cls.resource, ":", cls.action), String()).label(
            "scope"
        )

    def __str__(self):
        return f"{self.resource}:{self.action}"

    def __repr__(self):
        return f"<Permission(resource={self.resource}, action={self.action})>"
