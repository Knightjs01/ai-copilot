import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MessageThread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One thread per Shadow application, created implicitly on whichever side sends first (see
    MessageService.send_as_candidate/send_as_company) -- never pre-provisioned. No SoftDeleteMixin
    -- only an explicit project purge removes these rows (see project_deletion/service.py)."""

    __tablename__ = "message_threads"

    shadow_application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shadow_applications.id"), unique=True, index=True
    )
    # Denormalized from the job for RLS on the company path -- same rationale as shadow_jobs/
    # shadow_reveal/passport_matching's own company_id columns.
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    # "Company read" is shared across the whole hiring team, not per-user -- see module docstring.
    candidate_last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    company_last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Message(UUIDPrimaryKeyMixin, Base):
    """Immutable, append-only -- no edit/delete in this phase, no TimestampMixin (matches
    PassportVersion's "no TimestampMixin, just one creation timestamp" precedent for a row that's
    never updated). `ondelete="CASCADE"` on thread_id means a project purge only needs to delete
    MessageThread rows for the purged applications; Postgres cascades their Message children."""

    __tablename__ = "messages"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("message_threads.id", ondelete="CASCADE"), index=True
    )
    sender_type: Mapped[str] = mapped_column(String(20))  # "company" | "candidate"
    sender_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    sender_candidate_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
