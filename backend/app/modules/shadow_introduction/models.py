import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IntroductionRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class IntroductionRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """No SoftDeleteMixin -- append-only, same as TalentPoolGrant/ShadowRevealRequest: a request
    and its outcome are part of the permanent audit trail.

    Always job-scoped (shadow_job_id is required, not nullable) -- matches how candidate search
    itself is job-scoped (PassportMatchingService.search_candidates_for_job); there is no
    generic, job-less candidate browse in this product today.

    resulting_application_id is set once, only on acceptance -- see
    ShadowJobService.create_application_from_introduction. A decline does not permanently block a
    future fresh request for the same (candidate, company, job): only a still-pending or already-
    accepted row counts as "active" for the duplicate-request guard (see
    IntroductionRequestRepository.get_active_by_triple), mirroring TalentPoolGrant's exact
    precedent."""

    __tablename__ = "shadow_introduction_requests"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    shadow_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shadow_jobs.id"), index=True
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=IntroductionRequestStatus.PENDING.value)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resulting_application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shadow_applications.id", ondelete="SET NULL"),
        nullable=True,
    )
