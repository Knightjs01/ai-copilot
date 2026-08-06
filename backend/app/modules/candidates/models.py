import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CandidateSource(str, enum.Enum):
    REFERRAL = "referral"
    JOB_BOARD = "job_board"
    AGENCY = "agency"
    DIRECT = "direct"
    OTHER = "other"


class CandidateStatus(str, enum.Enum):
    NEW = "new"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class PrescreenOutcome(str, enum.Enum):
    ADVANCE = "advance"
    REJECT = "reject"
    HOLD = "hold"


class Candidate(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "candidates"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default=CandidateSource.DIRECT.value)
    status: Mapped[str] = mapped_column(String(20), default=CandidateStatus.NEW.value)
    resume_file_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interview_scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    prescreen_outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prescreen_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Captured alongside the prescreen outcome — expected_salary only makes sense once a real
    # conversation has happened; agency_name is only meaningful when source == AGENCY, but left
    # unconstrained at the DB level (same pattern as every other optional scalar in this table).
    expected_salary: Mapped[int | None] = mapped_column(nullable=True)
    agency_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
