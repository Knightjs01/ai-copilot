"""Hiring Project Kanban Merge: shadow_applications.pipeline_stage -- recruiter-set hiring-
pipeline progress for a Shadow applicant (new/screening/interviewing/offer/hired/rejected),
independent of the existing status column (which tracks identity-reveal workflow state only).
Backfills existing rows to "new" via server_default.

Revision ID: 0049
Revises: 0048
Create Date: 2026-08-22

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0049"
down_revision: str | None = "0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shadow_applications",
        sa.Column("pipeline_stage", sa.String(length=20), nullable=False, server_default="new"),
    )


def downgrade() -> None:
    op.drop_column("shadow_applications", "pipeline_stage")
