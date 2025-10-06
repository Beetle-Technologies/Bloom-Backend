import base64
import hashlib
import re
from typing import ClassVar
from uuid import UUID

from sqlmodel import Field
from src.core.types import GUID, IDType


class FriendlyMixin:
    """
    Mixin to add Rails-like friendly id functionality to SQLModel classes.
    Generates human-readable identifiers from database IDs (int or UUID).

    Attributes:
        friendly_id (str): A human-friendly version of the ID.
        slug (str, optional): A URL-friendly slug in format "id-name" (when enable_slug=True).
    """

    _ALPHABET: ClassVar[str] = "23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ"
    _MIN_LENGTH: ClassVar[int] = 6
    _MAX_LENGTH: ClassVar[int] = 12

    ENABLE_FRIENDLY_ID: ClassVar[bool] = True
    ENABLE_FRIENDLY_SLUG: ClassVar[bool] = False

    friendly_id: str | None = Field(index=True, unique=True, default=None)
    friendly_slug: str | None = Field(index=True, unique=True, default=None)

    @classmethod
    def to_friendly_id(cls, id_value: int | UUID) -> str:
        """Convert a database ID to a short, human-friendly string."""
        if isinstance(id_value, int):
            friendly = cls._encode_int(id_value)
            prefix = "i"
        elif isinstance(id_value, UUID):
            friendly = cls._encode_uuid(id_value)
            prefix = "u"
        elif isinstance(id_value, str) or isinstance(id_value, GUID):
            friendly = cls._encode_str(id_value)
            prefix = "s"
        else:
            raise TypeError(f"ID must be int or UUID, got {type(id_value).__name__}")

        result = f"{prefix}{friendly}"
        return result

    @classmethod
    def _encode_int(cls, value: int) -> str:
        """Encode an integer as a short string."""

        value = abs(value)

        chars = []
        base = len(cls._ALPHABET)

        while value > 0 or len(chars) < cls._MIN_LENGTH - 1:  # -1 to account for prefix
            chars.append(cls._ALPHABET[value % base])
            value //= base
            if value == 0 and len(chars) >= cls._MIN_LENGTH - 1:
                break

        result = "".join(reversed(chars))
        if len(result) > cls._MAX_LENGTH - 1:
            prefix_len = cls._MAX_LENGTH - 6
            hash_part = hashlib.md5(result.encode()).hexdigest()[:5]
            result = result[:prefix_len] + hash_part

        return result

    @classmethod
    def _encode_str(cls, value: str | GUID) -> str:
        """Encode a string as a short string."""
        bytes = value.encode("utf-8")
        return cls._encode_int(int.from_bytes(bytes, "big"))

    @classmethod
    def _encode_uuid(cls, uuid_value: UUID) -> str:
        """Encode a UUID as a short string."""

        uuid_bytes = uuid_value.bytes

        short_bytes = uuid_bytes[:8]

        encoded = base64.urlsafe_b64encode(short_bytes).decode("ascii").rstrip("=")

        result = "".join(cls._ALPHABET[ord(c) % len(cls._ALPHABET)] for c in encoded)

        while len(result) < cls._MIN_LENGTH - 1:
            result += cls._ALPHABET[0]

        if len(result) > cls._MAX_LENGTH - 1:
            result = result[: cls._MAX_LENGTH - 1]

        return result

    @classmethod
    def to_slug(cls, id_value: IDType, name_value: str) -> str:
        """
        Convert ID and name to a URL-friendly slug in format "id-name".

        Args:
            id_value: The model's ID (int or UUID)
            name_value: The name/title to slugify

        Returns:
            str: A slug in format "id-cleaned_name" (max 100 chars)
        """

        if isinstance(id_value, UUID):
            id_str = str(id_value).replace("-", "")[:8]  # Use first 8 chars of UUID
        elif isinstance(id_value, GUID):
            id_str = id_value.split("/")[-1]
        else:
            id_str = str(id_value)

        cleaned_name = re.sub(r"[^a-zA-Z0-9\s-]", "", name_value)
        cleaned_name = re.sub(r"\s+", "-", cleaned_name.strip())
        cleaned_name = cleaned_name.lower()
        cleaned_name = cleaned_name.strip("-")

        slug = f"{id_str}-{cleaned_name}"

        if len(slug) > 100:
            available_space = 100 - len(id_str) - 1
            if available_space > 0:
                slug = f"{id_str}-{cleaned_name[:available_space]}"
            else:
                slug = id_str[:100]

        return slug

    def get_friendly_id(self) -> str:
        """Get the friendly ID for this model instance."""

        id_value = getattr(self, "id", None)
        if id_value is None:
            raise ValueError("Model instance has no 'id' attribute")
        return self.to_friendly_id(id_value)

    def set_friendly_id(self) -> str:
        """Update the friendly_id field and return the new value."""

        if not self.ENABLE_FRIENDLY_ID:
            return ""
        self.friendly_id = self.get_friendly_id()
        return self.friendly_id

    def get_slug(self) -> str:
        """
        Get the slug for this model instance.
        Looks for 'name' or 'title' fields on the model.
        """

        if not self.ENABLE_FRIENDLY_SLUG:
            raise ValueError("Slug generation is disabled. Set ENABLE_FRIENDLY_SLUG=True on the class.")

        id_value = getattr(self, "id", None)
        if id_value is None:
            raise ValueError("Model instance has no 'id' attribute")

        name_value = getattr(self, "name", None) or getattr(self, "title", None)
        if name_value is None:
            raise ValueError("Model instance must have either 'name' or 'title' attribute for slug generation")

        return self.to_slug(id_value, name_value)

    def set_slug(self) -> str:
        """Update the slug field and return the new value."""

        if not self.ENABLE_FRIENDLY_SLUG:
            return ""
        self.friendly_slug = self.get_slug()
        return self.friendly_slug

    def save_friendly_fields(self):
        """
        Update both friendly_id and slug fields if enabled.
        """

        if self.ENABLE_FRIENDLY_ID:
            self.set_friendly_id()
        if self.ENABLE_FRIENDLY_SLUG:
            self.set_slug()
