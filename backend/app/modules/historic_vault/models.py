import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PurgedProjectRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only — never updated or soft-deleted, same reasoning as IdentityRevealEvent. Written
    once, at burn time, by ProjectDeletionService. project_id deliberately has no ForeignKey: the
    project row it refers to is gone by the time this row exists, so a constraint here would never
    be satisfiable. purged_by_email is denormalized rather than an actor_user_id FK — the whole
    point of this table is to outlive the rows it describes, and a removed/renamed team member
    shouldn't blank out who did the purge."""

    __tablename__ = "purged_project_records"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    project_title: Mapped[str] = mapped_column(String(255))
    candidate_count: Mapped[int] = mapped_column(Integer)
    data_categories_destroyed: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    purged_by_email: Mapped[str] = mapped_column(String(320))
    purged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
