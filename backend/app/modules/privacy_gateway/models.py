import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class SanitizedProfile(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "sanitized_profiles"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), unique=True, index=True
    )
    redacted_text: Mapped[str] = mapped_column(Text)
    redaction_counts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_file_type: Mapped[str] = mapped_column(String(10))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
