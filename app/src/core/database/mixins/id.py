from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

import inflection
from pydantic import field_validator
from sqlalchemy.orm import declared_attr
from sqlmodel import Field, SQLModel
from src.core.types import GUID


class BaseIDMixin(SQLModel):
    """
    A base mixin for models with a primary key.\n

    This mixin is used to define the primary key field for SQLModel models.
    It can be extended to create specific ID types (e.g., Integer, UUID, String).
    """

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return inflection.pluralize(inflection.underscore(cls.__name__))


class IntegerIDMixin(BaseIDMixin):
    """
    A mixin for models with an integer primary key.

    Attributes:\n
        id (int): The primary key field.
    """

    id: int = Field(index=True, primary_key=True)


class UUIDMixin(BaseIDMixin):
    """
    A mixin for models with a UUID primary key.

    Attributes:\n
        id (UUID): The primary key field.
    """

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )


class StringIDMixin(BaseIDMixin):
    """
    A mixin for models with a string primary key.

    Attributes:\n
        id (str): The primary key field.
    """

    id: str = Field(primary_key=True, index=True)


class GUIDMixin(BaseIDMixin):
    """
    A mixin for models with GUID primary keys.\n

    GUIDs follow the format: gid://{AppName}/{ResourceType}/{base64_encoded_id}
    This mixin generates GUIDs that mimic this structure.

    Attributes:\n
        id (GUID): The GUID primary key field.
    """

    id: GUID = Field(
        default=None,
        primary_key=True,
        index=True,
        nullable=False,
    )

    def __init__(self, **data):
        if "id" not in data or data["id"] is None:
            data["id"] = self.encode_guid()
        super().__init__(**data)

    @classmethod
    def encode_guid(cls) -> str:
        """
        Generate a GUID.

        Format: gid://{AppName}/{ResourceType}/{base64_encoded_id}

        Returns:
            str: A GUID
        """

        return GUID.encode_guid(resource_type=cls.__name__)

    @classmethod
    def decode_guid(cls, guid: str) -> dict[str, str]:
        """
        Decode a GUID to extract its components.

        Args:
            guid (str): The GUID to decode

        Returns:
            dict: Dictionary containing 'resource_type' and 'encoded_id'

        Raises:
            ValueError: If the GUID format is invalid
        """

        return GUID.decode_guid(guid=guid)


T = TypeVar("T")


class CompositeIDMixin(BaseIDMixin, Generic[T]):
    """
    A mixin for models with composite primary keys.\n

    This mixin provides methods for handling composite keys properly in SQLModel.
    The generic type T should be a tuple of the types of your primary key fields.

    Attributes:\n
        id (T): The composite primary key field.
    """

    @classmethod
    def get_composite_key_fields(cls) -> list[str]:
        """Return a list of field names that form the composite primary key."""

        model_fields = cls.model_fields
        return [
            field_name
            for field_name, field in model_fields.items()
            if field.json_schema_extra and dict(getattr(field, "json_schema_extra", {})).get("primary_key", False)
        ]

    def get_composite_key(self) -> T:
        """Get the composite key as a tuple of values."""

        key_fields = self.get_composite_key_fields()
        return tuple(getattr(self, field) for field in key_fields)  # type: ignore

    @field_validator("*", mode="before")
    @classmethod
    def validate_composite_keys(cls, v: Any, info: Any) -> Any:
        field_name = info.field_name
        field = cls.model_fields.get(field_name)
        if not field:
            return v

        # NOTE: Here we skip validation for non-primary key fields
        if not (field.json_schema_extra and dict(getattr(field, "json_schema_extra", {})).get("primary_key", False)):
            return v

        if v is None:
            raise ValueError(f"Primary key field '{field_name}' cannot be None")

        return v
