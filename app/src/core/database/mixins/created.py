from datetime import datetime

from sqlmodel import TIMESTAMP, Field, func


class CreatedDateTimeMixin:
    """
    Mixin that adds created datetime columns to a model

    Attributes:
        created_datetime (datetime): The datetime when the record was created.
    """

    created_datetime: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=False,
        sa_column_kwargs={"server_default": func.now()},
    )
