import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Interview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One row per scheduled interview -- an application can have several (multiple rounds), so
    shadow_application_id is indexed but NOT unique, unlike MessageThread."""

    __tablename__ = "interviews"

    shadow_application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shadow_applications.id"), index=True
    )
    # Denormalized from the job for RLS on the company path -- same rationale as MessageThread's
    # own company_id column.
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # "scheduled" | "cancelled" | "completed" -- see schemas.InterviewStatus.
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    scheduled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
