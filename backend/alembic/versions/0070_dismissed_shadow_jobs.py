"""Dismissed Jobs: a candidate's private "not interested" list on the Shadow job board.

No RLS -- this table has no company_id column, candidates aren't tenant-scoped. Explicit
GRANT needed regardless of migration 0001's `ALTER DEFAULT PRIVILEGES`, same pattern
migration 0033 (saved_shadow_jobs) already uses.

Revision ID: 0070
Revises: 0069
Create Date: 2026-08-31

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0070"
down_revision: str | None = "0069"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dismissed_shadow_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column(
            "shadow_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_jobs.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "candidate_user_id", "shadow_job_id", name="uq_dismissed_job_candidate_job"
        ),
    )
    op.create_index(
        "ix_dismissed_shadow_jobs_candidate_user_id", "dismissed_shadow_jobs", ["candidate_user_id"]
    )
    op.create_index(
        "ix_dismissed_shadow_jobs_shadow_job_id", "dismissed_shadow_jobs", ["shadow_job_id"]
    )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON dismissed_shadow_jobs TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.drop_table("dismissed_shadow_jobs")
