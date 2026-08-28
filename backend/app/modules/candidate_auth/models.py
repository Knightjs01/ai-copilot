import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CandidateUser(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Deliberately has no company_id — see this module's __init__.py. first_name/last_name are
    collected at signup specifically so phantom_passport's CV-parsing pipeline always has a
    known_full_name to hand to the existing redact_text() before any resume text reaches an LLM —
    the candidate never has to re-type their name for redaction to work (see the full_name
    property below, which reconstructs that single string for every internal caller that still
    wants one, e.g. WebAuthn's display name)."""

    __tablename__ = "candidate_users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255))
    # Nullable -- a candidate genuinely may have only one name (a mononym); never force a value
    # here that isn't real.
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(String(255), nullable=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() if self.last_name else self.first_name


class CandidateMfaBackupCode(UUIDPrimaryKeyMixin, Base):
    """Same single-use recovery-code pattern as auth.models.MfaBackupCode, scoped to a candidate
    instead of a company user. No company_id here — candidates have none, see this module's
    __init__.py — so there is nothing to key an RLS policy on; this table (like every other
    candidate_auth table) relies purely on application-layer scoping."""

    __tablename__ = "candidate_mfa_backup_codes"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    code_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CandidateRefreshToken(UUIDPrimaryKeyMixin, Base):
    """Same session-tracking shape as auth.models.RefreshToken — see that model's docstring."""

    __tablename__ = "candidate_refresh_tokens"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CandidateVerificationToken(UUIDPrimaryKeyMixin, Base):
    """Email-verification tokens for candidates. Unlike auth.models.VerificationToken (which
    serves email-verify/password-reset/invite via a `purpose` column), candidates only need this
    for one thing today -- a single-purpose table is simpler and honest about current scope
    rather than building a generic multi-purpose token system nothing else here needs yet."""

    __tablename__ = "candidate_verification_tokens"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CandidateWebAuthnCredential(UUIDPrimaryKeyMixin, Base):
    """Same shape as auth.models.WebAuthnCredential, scoped to a candidate instead of a company
    user. No company_id — candidates have none — so this relies on application-layer scoping
    like every other candidate_auth table."""

    __tablename__ = "candidate_webauthn_credentials"

    candidate_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_users.id"), index=True
    )
    credential_id: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    public_key: Mapped[str] = mapped_column(Text)
    sign_count: Mapped[int] = mapped_column(Integer, default=0)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
