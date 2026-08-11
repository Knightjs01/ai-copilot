import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    ON_HOLD = "on_hold"
    FILLED = "filled"
    CANCELLED = "cancelled"


class Project(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "projects"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ProjectStatus.DRAFT.value)
    hiring_manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


class ProjectMember(UUIDPrimaryKeyMixin, Base):
    """Resource-level authorization: a Member-role user can only act on a project (and its
    candidates) if a row exists here for them. Owner/Admin bypass this check entirely — they
    keep company-wide access, matching how those roles already work everywhere else. Denormalizes
    company_id so RLS can scope this table the same way as every other tenant-owned table."""

    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_members"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
