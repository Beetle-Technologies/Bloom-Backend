from sqlalchemy import TEXT
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlmodel import Field


class SearchableMixin:
    """
    Mixin for models that support full-text search.

    Attributes:\n
        search_text (str | None): The search text for full-text search.
        search_vector (str | None): The search vector for full-text search.
    """

    search_text: str | None = Field(
        sa_type=TEXT(),  # type: ignore[assignment]
        nullable=True,
        default=None,
    )

    search_vector: str | None = Field(
        sa_type=TSVECTOR(),  # type: ignore[assignment]
        default=None,
        nullable=True,
    )
