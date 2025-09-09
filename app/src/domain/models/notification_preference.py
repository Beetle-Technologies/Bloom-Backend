from typing import TYPE_CHECKING

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship
from src.core.database.mixins import GUIDMixin, TimestampMixin
from src.core.types import GUID
from src.libs.notifications import NotificationDeliveryMethod

if TYPE_CHECKING:
    from src.domain.models import AccountTypeInfo


class NotificationPreference(GUIDMixin, TimestampMixin, table=True):
    """
    Represents notification preferences for an account type info.

    Attributes:
        id (GUID): The unique identifier.
        account_type_info_id (GUID): Linked to AccountTypeInfo.
        enabled_methods (list[DeliveryMethod]): Enabled delivery methods.
        created_datetime (datetime): When created.
        updated_datetime (datetime | None): When updated.
    """

    SELECTABLE_FIELDS = [
        "id",
        "account_type_info_id",
        "enabled_methods",
        "is_enabled",
        "created_datetime",
        "updated_datetime",
    ]

    account_type_info_id: GUID = Field(
        foreign_key="account_type_infos.id", nullable=False, index=True
    )
    enabled_methods: dict[NotificationDeliveryMethod, bool] = Field(
        sa_column=Column(
            JSONB,
            nullable=False,
            default={
                NotificationDeliveryMethod.DATABASE: True,
                NotificationDeliveryMethod.EMAIL: True,
                NotificationDeliveryMethod.PUSH: False,
            },
        )
    )

    # Relationships
    account_type_info: "AccountTypeInfo" = Relationship(
        back_populates="notification_preferences"
    )
