import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TalentPoolGrantStatus(str, enum.Enum):
    REQUESTED = "requested"
    GRANTED = "granted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


class TalentPoolScope(str, enum.Enum):
    PROJECT_ONLY = "project_only"
    COMPANY_WIDE = "company_wide"


class TalentPoolGrant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """No SoftDeleteMixin — append-only, same reasoning as ShadowRevealRequest: a request and its
    outcome are part of the permanent audit trail, never deleted except by a company-level purge
    (which doesn't exist yet for this table, deliberately — see talent_pool/__init__.py)."""

    __tablename__ = "talent_pool_grants"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    # Nullable + SET NULL: a project burn deletes the ShadowApplication row this references, but
    # the grant itself must survive that (see __init__.py) — source_role_title below keeps the
    # human-readable context once this goes null.
    source_shadow_application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shadow_applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Which ATS project (if any) the source ShadowJob was linked to at request time -- lets a
    # project_only grant be matched against a NEW job later, if that new job is linked to the
    # same project (see passport_matching.service.search_talent_pool_for_job). Same nullable +
    # SET NULL treatment as source_shadow_application_id above, for the same reason: a project
    # burn must not break this FK, and once it goes null there's honestly no "this project" left
    # for a project_only grant to match against.
    source_project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_role_title: Mapped[str] = mapped_column(String(255))
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    # Set by the CANDIDATE at grant time (their choice, not the company's ask) — mirrors
    # RevealDecision.disclosure_level being the responder's call, not the requester's.
    scope: Mapped[str] = mapped_column(String(20), default=TalentPoolScope.PROJECT_ONLY.value)
    status: Mapped[str] = mapped_column(String(20), default=TalentPoolGrantStatus.REQUESTED.value)
    # Fixed for Phase 1 — not yet a real configurable taxonomy (see talent_pool/__init__.py and
    # the roadmap's later "retention policy engine" phase).
    purpose: Mapped[str] = mapped_column(String(50), default="future_role_matching")
    lawful_basis: Mapped[str] = mapped_column(String(20), default="consent")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Stored only, +12 months from grant — nothing enforces this yet (Phase 1 has no retention
    # policy engine), it's the honest first field of one.
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
