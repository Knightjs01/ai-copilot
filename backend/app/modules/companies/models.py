import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
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


class CompanyStatus(str, enum.Enum):
    """A company only ever comes into existence already APPROVED (see
    company_access.service.CompanyAccessRequestService.approve_request — there is no public
    self-service path to create one at all anymore). SUSPENDED is a later, Phantom-staff-only
    action; blocked at the single get_current_user_model choke point in auth/dependencies.py, not
    swept across individual routes. Distinct from CompanyProfileStatus below -- this suspends the
    whole workspace, that one only suspends the public profile page."""

    APPROVED = "approved"
    SUSPENDED = "suspended"


class CompanyProfileStatus(str, enum.Enum):
    """Replaces the old flat is_profile_public boolean. DRAFT/PENDING_REVIEW/LIVE/PAUSED are
    reachable via the company's own actions; SUSPENDED is platform-admin-only (mirrors
    CompanyStatus.SUSPENDED's precedent, scoped to just the profile page). "Approved" and "live"
    are deliberately the same transition, not two separate states -- mirrors
    PhantomPassport.approve_passport()'s own atomic approve-and-become-current-version design, no
    separate "approved but not yet visible" limbo state."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    LIVE = "live"
    PAUSED = "paused"
    SUSPENDED = "suspended"


class Company(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Both computed once at signup from the owner's email — see
    # app/modules/companies/domain_verification.py for what "verified" means here (a denylist
    # check, not real domain ownership verification).
    email_domain: Mapped[str] = mapped_column(String(255), default="")
    is_verified_domain: Mapped[bool] = mapped_column(Boolean, default=False)

    # Live, editable draft fields -- never shown directly to a candidate. GET /companies/{slug}
    # reads from current_profile_version_id's immutable snapshot instead, so a company can keep
    # editing without touching what's currently public. See CompanyProfileVersion below.
    description: Mapped[str | None] = mapped_column(Text, default=None)
    culture: Mapped[str | None] = mapped_column(Text, default=None)
    benefits: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    size: Mapped[str | None] = mapped_column(String(20), default=None)
    industry: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    logo_storage_key: Mapped[str | None] = mapped_column(String(512), default=None)
    cover_image_storage_key: Mapped[str | None] = mapped_column(String(512), default=None)
    hiring_process_overview: Mapped[str | None] = mapped_column(Text, default=None)

    profile_status: Mapped[str] = mapped_column(
        String(20), default=CompanyProfileStatus.DRAFT.value
    )
    current_profile_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("company_profile_versions.id"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(20), default=CompanyStatus.APPROVED.value)

    # Commercial Phase 1 -- see app/modules/commercial/. commercial_plan_id is nullable only
    # because SQLAlchemy models can't express "always backfilled" the way the migration's own
    # UPDATE does; every real company row has one from the moment this shipped.
    # active_role_limit_override is genuinely optional -- most companies just use their plan's
    # own default and never get one.
    commercial_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commercial_plans.id"), nullable=True
    )
    active_role_limit_override: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Company Profile Visual Rebuild -- see the plan this shipped under. tagline/website/
    # founded_year/headquarters are plain "who we are" facts with no precedent elsewhere.
    # values/hiring_highlights mirror benefits/industry's existing JSONB-list pattern, just with
    # {title, body} objects instead of plain strings.
    tagline: Mapped[str | None] = mapped_column(String(255), default=None)
    website: Mapped[str | None] = mapped_column(String(255), default=None)
    founded_year: Mapped[int | None] = mapped_column(Integer, default=None)
    headquarters: Mapped[str | None] = mapped_column(String(255), default=None)
    # Distinct from `size` (a coarse public-facing band, e.g. "51-200") -- this is a precise,
    # company-entered headcount, internal-only (see ProfileStats.team_size's docstring): the
    # count of Phantom Hire logins is a completely different, smaller number than a company's
    # real employee count, and conflating the two was a real bug caught before this shipped.
    employee_count: Mapped[int | None] = mapped_column(Integer, default=None)
    # Deliberately distinct from is_verified_domain above (an automatic denylist heuristic, not a
    # real check) -- this is the one honest "Phantom verified this employer" signal, settable only
    # by a platform admin. Never present in CompanyUpdate; a company can never set this on itself.
    is_verified_employer: Mapped[bool] = mapped_column(Boolean, default=False)
    values: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    looking_for: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    hiring_highlights: Mapped[list[Any]] = mapped_column(JSONB, default=list)


class CompanyProfileVersion(UUIDPrimaryKeyMixin, Base):
    """An immutable snapshot, created only on an explicit platform-admin approval — mirrors
    PassportVersion exactly (same reasoning: one JSONB blob per version, not one column per
    field, so the public shape can evolve without a migration touching every historical row).
    approved_by_admin_id is nullable to allow a migration-time grandfather backfill for companies
    that were already public before this table existed, with no real admin behind that state. No
    TimestampMixin -- approved_at is the only timestamp that matters for a row that's never
    updated."""

    __tablename__ = "company_profile_versions"
    __table_args__ = (UniqueConstraint("company_id", "version_number"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    approved_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), nullable=True
    )
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
