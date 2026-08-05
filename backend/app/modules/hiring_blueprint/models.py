import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class HiringBlueprint(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "hiring_blueprints"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), unique=True, index=True
    )
    role_summary: Mapped[str] = mapped_column(Text)
    key_responsibilities: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    must_have_qualifications: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    nice_to_have_qualifications: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    evaluation_criteria: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    model_used: Mapped[str] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
