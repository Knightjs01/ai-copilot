import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DismissedShadowJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dismissed_shadow_jobs"
    __table_args__ = (
        UniqueConstraint(
            "candidate_user_id", "shadow_job_id", name="uq_dismissed_job_candidate_job"
        ),
    )

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    shadow_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shadow_jobs.id"), index=True
    )
