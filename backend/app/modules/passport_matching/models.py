import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PassportJobMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Cached AI match result for one (passport_version, shadow_job) pair — the first two-FK
    AI-result cache table in this codebase (every other one, e.g. InterviewKit, upserts on a
    single FK). `shadow_job_updated_at` is a snapshot of the job's own `updated_at` at scoring
    time, since ShadowJob has no version table of its own — a mismatch on read means the job
    changed since this row was computed, and the service recomputes rather than serving it.

    No SoftDeleteMixin — a stale/superseded row is just recomputed in place (upsert), never
    soft-deleted; only an explicit project purge removes rows outright (see
    project_deletion/service.py)."""

    __tablename__ = "passport_job_matches"
    __table_args__ = (UniqueConstraint("passport_version_id", "shadow_job_id"),)

    passport_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("passport_versions.id"), index=True
    )
    shadow_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shadow_jobs.id"), index=True
    )
    # Denormalized from the job — this table is structurally dual-audience like shadow_jobs
    # itself (a company's job + a candidate's own passport), so it carries company_id for a
    # future company-side RLS-scoped read, even though every candidate-facing read in this
    # module bypasses RLS via app_auth and filters explicitly by passport ownership instead
    # (same rationale as shadow_jobs/__init__.py's).
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))

    match_tier: Mapped[str] = mapped_column(String(30))
    match_score: Mapped[int] = mapped_column(Integer)
    strengths: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    gaps: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    summary: Mapped[str] = mapped_column(Text)

    shadow_job_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    model_used: Mapped[str] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
