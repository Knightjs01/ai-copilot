import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CandidateIdentityVault(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "candidate_identity_vaults"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), unique=True, index=True
    )
    # Denormalized off Candidate — the project vault list / dashboard queries filter by project
    # without needing a join back through candidates for every row.
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    full_name_encrypted: Mapped[str] = mapped_column(Text)
    email_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_employer_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_title_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)


class IdentityRevealEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only audit record of a single identity reveal — no SoftDeleteMixin, these are only
    ever hard-deleted as part of a project burn. created_at (from TimestampMixin) doubles as
    "revealed_at"; duration/closed_at get filled in by a second call once the recruiter dismisses
    the reveal popup."""

    __tablename__ = "identity_reveal_events"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
