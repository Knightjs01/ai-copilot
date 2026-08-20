"""Job Alerts: a candidate's saved search criteria on the Shadow job board.

No RLS -- this table has no company_id column, candidates aren't tenant-scoped. Explicit GRANT,
same pattern migration 0033 already uses for saved_shadow_jobs.

Revision ID: 0039
Revises: 0038
Create Date: 2026-08-24

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("seniority", sa.String(100), nullable=True),
        sa.Column("remote_preference", sa.String(20), nullable=True),
        sa.Column("employment_type", sa.String(20), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_job_alerts_candidate_user_id", "job_alerts", ["candidate_user_id"])

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON job_alerts TO app_runtime, app_auth")


def downgrade() -> None:
    op.drop_table("job_alerts")
