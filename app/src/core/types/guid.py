import base64
import struct
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError, core_schema


class GUID(str):
    """
    Pydantic type for GUID (Global Unique Identifier) strings.\n

    GUIDs follow the format: gid://{AppName}/{ResourceType}/{base64_encoded_id}

    This type validates GUID format and provides methods for encoding/decoding.
    """

    _APP_NAME: ClassVar[str] = "bloom"

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema.update(
            type="string",
            pattern=rf"^gid://{cls._APP_NAME}/[a-zA-Z0-9_]+/[a-zA-Z0-9+/]+$",
            example=f"gid://{cls._APP_NAME}/Account/dGVzdGluZ3Rlc3Rpbmc",
            description=f"GUID in format gid://{cls._APP_NAME}/ResourceType/base64_encoded_id",
        )
        return json_schema

    @classmethod
    def validate(cls, value: Any) -> "GUID":
        errors = []

        if not isinstance(value, str):
            errors.append(
                InitErrorDetails(
                    type=PydanticCustomError("value_error", "GUID should be a string"),
                    input=value,
                )
            )

        if isinstance(value, str) and not value.strip():
            errors.append(
                InitErrorDetails(
                    type=PydanticCustomError("value_error", "GUID cannot be empty"),
                    input=value,
                )
            )
        else:
            try:
                cls.decode_guid(value)
            except ValueError as e:
                errors.append(
                    InitErrorDetails(
                        type=PydanticCustomError(
                            "value_error",
                            "Invalid GUID format: {error}",
                            {"error": str(e)},
                        ),
                        input=value,
                    )
                )

        if errors:
            raise ValidationError.from_exception_data(
                title="invalid_guid",
                line_errors=errors,
            )

        return cls(value)

    @classmethod
    def encode_guid(cls, resource_type: str) -> "GUID":
        """
        Generate a new GUID for the given resource type.

        Args:
            resource_type: The type of resource (e.g., "User", "Product")

        Returns:
            GUID: A new GUID instance
        """
        if resource_type.endswith("Model"):
            resource_type = resource_type[:-5]

        unique_id = uuid4()
        int_id = unique_id.int

        id_bytes = struct.pack(">QQ", int_id >> 64, int_id & 0xFFFFFFFFFFFFFFFF)
        encoded_id = base64.b64encode(id_bytes).decode("ascii").rstrip("=")

        guid_str = f"gid://{cls._APP_NAME}/{resource_type}/{encoded_id}"
        return cls(guid_str)

    @classmethod
    def decode_guid(cls, guid: str) -> dict[str, str]:
        """
        Decode a GUID to extract its components.

        Args:
            guid: The GUID string to decode

        Returns:
            dict: Dictionary containing 'app_name', 'resource_type' and 'encoded_id'

        Raises:
            ValueError: If the GUID format is invalid
        """
        if not guid.startswith("gid://"):
            raise ValueError("GUID must start with 'gid://'")

        parts = guid[6:].split("/")
        if len(parts) != 3:
            raise ValueError("GUID must have format gid://app_name/resource_type/encoded_id")

        app_name, resource_type, encoded_id = parts

        if not all([app_name, resource_type, encoded_id]):
            raise ValueError("GUID parts cannot be empty")

        return {"app_name": app_name, "resource_type": resource_type, "encoded_id": encoded_id}

    @classmethod
    def extract_internal_id(cls, guid: str) -> UUID:
        """
        Extract the internal UUID from a GUID.

        Args:
            guid: The GUID string

        Returns:
            UUID: The internal UUID

        Raises:
            ValueError: If the GUID format is invalid or cannot be decoded
        """
        decoded = cls.decode_guid(guid)
        encoded_id = decoded["encoded_id"]

        padding = 4 - (len(encoded_id) % 4)
        if padding != 4:
            encoded_id += "=" * padding

        try:
            id_bytes = base64.b64decode(encoded_id)

            if len(id_bytes) != 16:
                raise ValueError("Invalid UUID bytes length")

            high, low = struct.unpack(">QQ", id_bytes)
            int_id = (high << 64) | low
            return UUID(int=int_id)
        except Exception as e:
            raise ValueError(f"Cannot decode GUID: {e}")

    def get_resource_type(self) -> str:
        """Get the resource type from this GUID."""
        return self.decode_guid(str(self))["resource_type"]

    def get_app_name(self) -> str:
        """Get the app name from this GUID."""
        return self.decode_guid(str(self))["app_name"]

    def to_uuid(self) -> UUID:
        """Convert this GUID to its internal UUID."""
        return self.extract_internal_id(str(self))

    def __repr__(self) -> str:
        return f"GUID('{str(self)}')"
