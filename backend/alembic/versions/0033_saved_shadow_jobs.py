"""Saved Jobs: a candidate's private bookmarks on the Shadow job board.

No RLS -- this table has no company_id column, candidates aren't tenant-scoped. An explicit
GRANT is needed regardless of migration 0001's `ALTER DEFAULT PRIVILEGES` (that default only
attaches to objects subsequently created by the same role that issued it; verified against a
real run that a new table here does NOT inherit it) -- same explicit-GRANT pattern migration
0017 already uses for shadow_jobs/shadow_applications.

Revision ID: 0033
Revises: 0032
Create Date: 2026-08-18

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_shadow_jobs",
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
        sa.Column("collection_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "candidate_user_id", "shadow_job_id", name="uq_saved_job_candidate_job"
        ),
    )
    op.create_index(
        "ix_saved_shadow_jobs_candidate_user_id", "saved_shadow_jobs", ["candidate_user_id"]
    )
    op.create_index("ix_saved_shadow_jobs_shadow_job_id", "saved_shadow_jobs", ["shadow_job_id"])

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON saved_shadow_jobs TO app_runtime, app_auth")


def downgrade() -> None:
    op.drop_table("saved_shadow_jobs")
