"""Phantom Command 2.0 Phase 6: a real in-app notification centre for platform admins.

Adds platform_admins.notifications_read_at (a single per-admin "unread since" watermark,
server-defaulted to now() so every existing admin starts with a clean slate rather than a
backlog of "unread" history) and a new platform_admin_notifications table -- a point-in-time
event feed, distinct from platform_admin_audit_logs (who-did-what) and the pull-based Action
Queue (live, pending-only, no table). required_permission is nullable (null = visible to every
admin); non-null values are checked against the caller's real permission set at read time.

No RLS, same reasoning as every other platform-admin table (single-tenant-global data). Excluded
from Danger Zone's purge automatically -- _PURGE_EXCLUDED_PREFIX = "platform_admin" already
matches this table by name, no purge-service change needed.

Revision ID: 0074
Revises: 0073
Create Date: 2026-09-04

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0074"
down_revision: str | None = "0073"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "platform_admins",
        sa.Column(
            "notifications_read_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "platform_admin_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.String(500), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("required_permission", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_platform_admin_notifications_action", "platform_admin_notifications", ["action"]
    )
    op.create_index(
        "ix_platform_admin_notifications_created_at",
        "platform_admin_notifications",
        ["created_at"],
    )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON platform_admin_notifications "
        "TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.drop_table("platform_admin_notifications")
    op.drop_column("platform_admins", "notifications_read_at")
