import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FRACTIONAL = "fractional"


class ShadowJobStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


class ShadowApplicationStatus(str, enum.Enum):
    """Only SUBMITTED/UNDER_REVIEW/DECLINED/WITHDRAWN are ever set by this module today.
    REVEAL_REQUESTED and REVEALED exist so the Reveal Request workflow (deferred — see
    shadow_jobs/__init__.py) can land as a status-transition feature, not a schema migration."""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    REVEAL_REQUESTED = "reveal_requested"
    REVEALED = "revealed"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


class ShadowJob(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "shadow_jobs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, unique=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    title: Mapped[str] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(20), default=EmploymentType.FULL_TIME.value)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_preference: Mapped[str | None] = mapped_column(String(20), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20), default=ShadowJobStatus.DRAFT.value)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ShadowApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """No SoftDeleteMixin — a withdrawn application is a status, not a deletion; the row (and
    its Callsign) stays put so a company's applicant list and audit trail stay consistent."""

    __tablename__ = "shadow_applications"
    __table_args__ = (
        UniqueConstraint(
            "shadow_job_id", "candidate_user_id", name="uq_shadow_application_job_candidate"
        ),
        UniqueConstraint("shadow_job_id", "callsign", name="uq_shadow_application_job_callsign"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    shadow_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shadow_jobs.id"), index=True
    )
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    phantom_passport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("phantom_passports.id")
    )
    # Null only for applications submitted before this column existed (pre-launch dev rows) —
    # every application going forward gets one, enforced in the service layer since the approval
    # gate it depends on didn't exist yet for those old rows. See phantom_passport/models.py's
    # PassportVersion for why this is what freezes a recruiter's view to apply-time content.
    passport_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("passport_versions.id"), nullable=True
    )
    callsign: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default=ShadowApplicationStatus.SUBMITTED.value)
