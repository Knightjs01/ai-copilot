import enum
import uuid
from datetime import date
from typing import Any

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
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
    address_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)


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
