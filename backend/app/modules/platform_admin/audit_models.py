import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin


class PlatformAdminAuditLog(UUIDPrimaryKeyMixin, Base):
    """Append-only audit trail for Phantom-staff actions -- a separate table from the
    company-scoped audit_logs (auth/../audit/models.py), which structurally cannot represent
    these: its company_id is NOT nullable (a Reject action has no company yet) and its actor FKs
    to users.id, not platform_admins.id. Same "separate principal needs separate infra" reasoning
    already applied to platform_admins itself."""

    __tablename__ = "platform_admin_audit_logs"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
