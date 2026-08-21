"""Platform Admin Audit Log: a separate, append-only audit trail for Phantom-staff actions
(access_request.approved/rejected/info_requested, company.suspended/reactivated).

The existing audit_logs table structurally cannot represent these -- its company_id is NOT
nullable (a Reject action has no company yet) and its actor FKs to users.id, not
platform_admins.id. No RLS -- not tenant data, same reasoning as platform_admins itself.

Revision ID: 0041
Revises: 0040
Create Date: 2026-08-26

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0041"
down_revision: str | None = "0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_admin_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "admin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admins.id"),
            nullable=False,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_platform_admin_audit_logs_admin_id", "platform_admin_audit_logs", ["admin_id"]
    )
    op.create_index("ix_platform_admin_audit_logs_action", "platform_admin_audit_logs", ["action"])

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON platform_admin_audit_logs TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.drop_table("platform_admin_audit_logs")
