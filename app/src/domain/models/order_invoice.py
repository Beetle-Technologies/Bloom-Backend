from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from pydantic import EmailStr
from sqlalchemy import TEXT, CheckConstraint
from sqlalchemy.dialects.postgresql import NUMERIC
from sqlmodel import TIMESTAMP, Column, Field, Relationship, func
from src.core.database.mixins import FriendlyMixin, GUIDMixin, TimestampMixin
from src.core.types import GUID, PhoneNumber

if TYPE_CHECKING:
    from src.domain.models import Order


class OrderInvoice(GUIDMixin, FriendlyMixin, TimestampMixin, table=True):
    """
    Represents an invoice generated from an order.

    Attributes:
        id (GUID): The unique identifier for the invoice.
        friendly_id (str): A friendly identifier for the invoice.
        order_id (GUID): ID of the associated order.
        status (InvoiceStatus): Current status of the invoice.
        subtotal (Decimal): Subtotal before tax and discounts.
        tax_amount (Decimal): Total tax amount.
        discount_amount (Decimal): Total discount amount.
        total_amount (Decimal): Final total amount (subtotal + tax - discount).
        amount_paid (Decimal): Total amount paid so far.
        amount_due (Decimal): Remaining amount to be paid.
        currency (str): Currency code (e.g., USD, NGN).
        issue_date (datetime): When the invoice was issued.
        paid_date (datetime | None): When the invoice was fully paid.
        notes (str | None): Additional notes or terms.
        billing_name (str): Name of the person/company being billed.
        billing_email (str): Email for billing.
        billing_phone (str | None): Phone number for billing.
        billing_address (str | None): Billing address.
        created_datetime (datetime): When created.
        updated_datetime (datetime | None): When last updated.
    """

    __tablename__ = "order_invoices"  # type: ignore[override]

    __table_args__ = (
        CheckConstraint(
            "amount_paid <= total_amount",
            name="chk_amount_paid_not_exceed_total",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="chk_total_amount_non_negative",
        ),
    )

    SELECTABLE_FIELDS: ClassVar[list[str]] = [
        "id",
        "friendly_id",
        "invoice_tag",
        "order_id",
        "status",
        "subtotal",
        "tax_amount",
        "discount_amount",
        "total_amount",
        "amount_paid",
        "currency",
        "issue_date",
        "paid_date",
        "billing_name",
        "billing_email",
        "created_datetime",
        "updated_datetime",
    ]

    order_id: GUID = Field(foreign_key="orders.id", nullable=False, index=True, unique=True)
    invoice_tag: str = Field(max_length=50, nullable=False, unique=True, index=True)

    subtotal: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00")))
    tax_amount: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00")))
    discount_amount: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00")))
    total_amount: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False))
    amount_paid: Decimal = Field(sa_column=Column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00")))

    currency: str = Field(max_length=3, nullable=False)

    issue_date: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=False,
        sa_column_kwargs={"server_default": func.now()},
    )
    paid_date: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[assignment]
        nullable=True,
        default=None,
    )

    notes: str | None = Field(sa_column=Column(TEXT(), nullable=True, default=None))

    billing_name: str = Field(max_length=255, nullable=False)
    billing_email: EmailStr = Field(max_length=255, nullable=False)
    billing_phone: PhoneNumber | None = Field(max_length=50, nullable=True, default=None)
    billing_address: str | None = Field(sa_column=Column(TEXT(), nullable=True, default=None))

    order: "Order" = Relationship(back_populates="invoice")

    def save_invoice_tag(self):
        if not self.friendly_id:
            raise ValueError("Friendly ID must be set before generating invoice number.")

        self.invoice_tag = f"INV-{datetime.now().strftime('%Y-%m-%d')}-{self.friendly_id.upper()}"
