import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CompanyBillingStatus(str, enum.Enum):
    """not_started: no checkout has ever been completed (the default for every company, since
    plans are admin-assigned with no payment attached at creation). active/past_due/canceled
    mirror the real Stripe subscription's own status, synced by billing.service's webhook
    handler -- never set by any code path other than a real Stripe event."""

    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class CompanyBilling(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """1:1 with Company, mirrors CompanyProfileVersion's own "separate concern, separate table"
    precedent rather than bloating Company itself. Created lazily -- the first time a company's
    Owner starts a checkout, not at company-creation time, since most of a company's lifetime
    with no Stripe interaction needs no row here at all."""

    __tablename__ = "company_billing"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), unique=True, index=True
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=CompanyBillingStatus.NOT_STARTED.value)
    billing_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
