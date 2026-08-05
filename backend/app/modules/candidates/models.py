import enum
import uuid

from sqlalchemy import ForeignKey, String
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
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
