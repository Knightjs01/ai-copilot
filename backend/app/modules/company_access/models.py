import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AccessRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CompanyAccessRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "company_access_requests"

    full_name: Mapped[str] = mapped_column(String(255))
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255))
    work_email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default=AccessRequestStatus.PENDING.value)
    reviewed_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Set once approved & provisioned -- the request's audit trail of which real Company it became.
    created_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
