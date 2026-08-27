"""Platform-admin MFA: mfa_enabled/mfa_secret_encrypted on platform_admins, plus a backup-codes
table -- mirrors the company-user MFA shape (users.mfa_enabled/mfa_secret_encrypted,
mfa_backup_codes) for the platform_admins principal, needed so Danger Zone can require a real
step-up (password + TOTP) before it's reachable at all, not just permission-gated.

No RLS on the new table, same reasoning as every other platform-admin table (single-tenant-global
data).

Revision ID: 0060
Revises: 0059
Create Date: 2026-08-27

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0060"
down_revision: str | None = "0059"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "platform_admins",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "platform_admins",
        sa.Column("mfa_secret_encrypted", sa.String(255), nullable=True),
    )

    op.create_table(
        "platform_admin_mfa_backup_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "admin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admins.id"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_platform_admin_mfa_backup_codes_admin_id",
        "platform_admin_mfa_backup_codes",
        ["admin_id"],
    )
    op.create_index(
        "ix_platform_admin_mfa_backup_codes_code_hash",
        "platform_admin_mfa_backup_codes",
        ["code_hash"],
        unique=True,
    )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON platform_admin_mfa_backup_codes "
        "TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.drop_table("platform_admin_mfa_backup_codes")
    op.drop_column("platform_admins", "mfa_secret_encrypted")
    op.drop_column("platform_admins", "mfa_enabled")
