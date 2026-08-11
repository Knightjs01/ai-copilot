import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CandidateUser(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Deliberately has no company_id — see this module's __init__.py. full_name is collected at
    signup (mirrors auth.User) specifically so phantom_passport's CV-parsing pipeline always has
    a known_full_name to hand to the existing redact_text() before any resume text reaches an
    LLM — the candidate never has to re-type their name for redaction to work."""

    __tablename__ = "candidate_users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)


class CandidateRefreshToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "candidate_refresh_tokens"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
