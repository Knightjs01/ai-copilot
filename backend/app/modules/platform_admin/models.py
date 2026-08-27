import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PlatformAdmin(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_admins"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PlatformAdminRefreshToken(UUIDPrimaryKeyMixin, Base):
    """Mirrors auth.models.RefreshToken's exact shape/rotation semantics for the platform-admin
    principal -- a platform admin's session must never be swappable with a company session's
    cookie or vice versa, same reasoning candidate_refresh_tokens is its own table. No
    user_agent/ip_address/last_used_at columns -- no "Active Sessions" UI is asked for on this
    single-admin tool yet; add them the same way auth.models.RefreshToken has them if that ever
    changes."""

    __tablename__ = "platform_admin_refresh_tokens"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlatformAdminRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Mirrors auth.models.Role, minus company_id -- platform admins aren't multi-tenant (one
    platform, not many companies each needing their own copy of a role), so a role name is
    globally unique rather than scoped per-company."""

    __tablename__ = "platform_admin_roles"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)


class PlatformAdminPermission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "platform_admin_permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255))


class PlatformAdminRolePermission(Base):
    __tablename__ = "platform_admin_role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admin_roles.id"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admin_permissions.id"), primary_key=True
    )


class PlatformAdminRoleAssignment(Base):
    """Mirrors auth.models.UserRole -- named distinctly (not "platform_admin_user_roles") to
    avoid any confusion with the company-user table of a similar shape."""

    __tablename__ = "platform_admin_role_assignments"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admin_roles.id"), primary_key=True
    )
