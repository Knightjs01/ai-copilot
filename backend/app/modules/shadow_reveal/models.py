import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RevealRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


class ShadowRevealRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """No SoftDeleteMixin — append-only, same as identity_vault.IdentityRevealEvent: a request
    and its outcome are part of the permanent audit trail, never deleted except by a project/
    company-level purge."""

    __tablename__ = "shadow_reveal_requests"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    shadow_application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shadow_applications.id"), unique=True, index=True
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=RevealRequestStatus.PENDING.value)
    # Set only when the candidate approves — the level they chose to disclose at. Null while
    # pending/declined, since there's nothing to disclose either way.
    disclosure_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
