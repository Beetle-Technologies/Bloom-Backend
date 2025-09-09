from src.core.database.mixins.created import CreatedDateTimeMixin
from src.core.database.mixins.updated import UpdatedDateTimeMixin


class TimestampMixin(CreatedDateTimeMixin, UpdatedDateTimeMixin):
    """
    Mixin that adds created and updated datetime columns to a model

    Attributes:\n
        created_datetime (datetime): The datetime when the record was created.
        updated_datetime (datetime | None): The datetime when the record was last updated.
    """

    pass
