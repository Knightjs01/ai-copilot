import enum
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CareerIntent(str, enum.Enum):
    ACTIVELY_LOOKING = "actively_looking"
    OPEN_TO_OPPORTUNITY = "open_to_opportunity"
    JUST_EXPLORING = "just_exploring"
    NOT_LOOKING = "not_looking"


class RemotePreference(str, enum.Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    FLEXIBLE = "flexible"


class VerificationStatus(str, enum.Enum):
    """Deliberately starts and stays UNVERIFIED until a real verification step exists — see
    phantom_passport/__init__.py. Never set to VERIFIED anywhere in this codebase yet."""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class PhantomPassport(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """The Shadow Profile — anonymous professional data only. No name, email, phone, or any
    other direct identifier lives on this table; that split is enforced at the schema level
    (see PassportPersonalInfo), not just by convention. One passport per candidate, reusable
    across every project they apply to — the opposite of the per-project Candidate record in
    app.modules.candidates, which is intentionally scoped to a single company's hiring project."""

    __tablename__ = "phantom_passports"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), unique=True, index=True
    )
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    industries: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_preference: Mapped[str | None] = mapped_column(String(20), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notice_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    career_intent: Mapped[str] = mapped_column(
        String(30), default=CareerIntent.JUST_EXPLORING.value
    )
    verification_status: Mapped[str] = mapped_column(
        String(20), default=VerificationStatus.UNVERIFIED.value
    )
    # Null until the candidate has explicitly approved a snapshot — see PassportVersion. This is
    # the only "is it approved" signal; a separate boolean would just be a second field that can
    # drift out of sync with this one.
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("passport_versions.id"), nullable=True
    )
    # Generated once, at first approval (see PhantomPassportService.approve_passport) — never
    # regenerated after that. A stable identity for the Passport itself, distinct from
    # shadow_jobs' per-application Callsigns (fresh for every job application, deliberately, so
    # applying to two roles never links back to the same person). Only ever returned to the
    # owning candidate via GET /phantom-passport/me — never added to any company-facing schema.
    callsign: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)


class PassportPersonalInfo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The Project Vault's master source — everything here is encrypted at rest with the same
    Fernet key as app.modules.identity_vault, and this table is never joined into any Shadow
    Profile, matching, or recruiter-facing query. It exists solely so the candidate's own
    Passport view can show them their own data, and so a future "Apply with Phantom Passport"
    flow has a single place to copy encrypted PII from into a project's per-project vault."""

    __tablename__ = "passport_personal_info"

    passport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("phantom_passports.id"), unique=True, index=True
    )
    legal_name_encrypted: Mapped[str] = mapped_column(Text)
    phone_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)


class PassportCareerEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """company_name_encrypted is the real employer — private, decrypted only for the owning
    candidate's own view. company_name_anonymized (e.g. "Global Payments Platform" instead of
    "Stripe") is what a Shadow Profile / recruiter card would ever display — see
    phantom_passport/__init__.py for why both fields exist on the same row rather than deriving
    one from the other at read time."""

    __tablename__ = "passport_career_entries"

    passport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("phantom_passports.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    company_name_encrypted: Mapped[str] = mapped_column(Text)
    company_name_anonymized: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    achievements: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class CandidateCvDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The original CV file the candidate uploaded — private to the candidate, never joined into
    any Shadow Profile or recruiter-facing query. One active document per candidate; a "Replace
    CV" upload deletes the old storage key and overwrites this row in place, matching
    app.modules.candidates.service.CandidateService.upload_resume's replace pattern. Reverses
    this module's original zero-file-retention design — see PassportVersion below for why."""

    __tablename__ = "candidate_cv_documents"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), unique=True, index=True
    )
    storage_key: Mapped[str] = mapped_column(String(512))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PassportVersion(UUIDPrimaryKeyMixin, Base):
    """An immutable snapshot, created only on an explicit candidate approval — never mutated
    after creation. `snapshot` deliberately holds only the same fields a ShadowProfile projects
    (see shadow_jobs/schemas.py) — safe-to-recruiter data, never PII, never a real employer name
    — so an already-submitted ShadowApplication can freeze to exactly what a recruiter saw at
    apply time, instead of shadow_jobs's live read silently rewriting history on every Passport
    edit. `schema_version` lives inside the JSONB blob itself so old snapshots stay renderable
    if ShadowProfile's shape ever changes. No TimestampMixin — approved_at is the only timestamp
    that matters for a row that's never updated."""

    __tablename__ = "passport_versions"
    __table_args__ = (UniqueConstraint("passport_id", "version_number"),)

    passport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("phantom_passports.id"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # A live join through this FK would be wrong the moment the CV is replaced — CandidateCvDocument
    # is mutated in place on replace (same row id, new content), so a joined "source filename"
    # would silently drift to whatever's most recently uploaded. source_cv_filename below is
    # captured by value at approval time instead; this FK is kept only so a still-existing
    # original file can be looked up for "view the CV this version was built from" — it goes
    # null on delete/replace without corrupting the historical record.
    source_cv_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_cv_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_cv_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
