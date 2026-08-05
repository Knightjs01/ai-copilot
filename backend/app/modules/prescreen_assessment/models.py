import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class PrescreenAssessment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "prescreen_assessments"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), unique=True, index=True
    )
    fit_rating: Mapped[str] = mapped_column(String(20))
    fit_summary: Mapped[str] = mapped_column(Text)
    strengths: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    gaps: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    suggested_questions: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    areas_to_probe: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    # Only populated by the second, post-call generation step (generate_handoff_recommendations)
    # — null until the TA has actually run the call and recorded prescreen_notes.
    handoff_recommendations: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
