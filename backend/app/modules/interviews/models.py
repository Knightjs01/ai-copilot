import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
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


class InterviewParticipant(UUIDPrimaryKeyMixin, Base):
    """Resource-level authorization for the Interviewer role: an Interviewer can only see an
    interview if a row exists here for them. Owner/TA Admin/Recruiter (anyone with
    interviews.schedule) bypass this entirely and keep unscoped company-wide visibility, matching
    ProjectMember's exact "org-wide roles bypass, everyone else needs an explicit row" shape."""

    __tablename__ = "interview_participants"
    __table_args__ = (
        UniqueConstraint("interview_id", "user_id", name="uq_interview_participants"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
