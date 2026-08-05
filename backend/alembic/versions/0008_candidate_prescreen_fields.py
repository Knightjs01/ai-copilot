"""Phase 8 (Part A): candidate pre-screen tracking fields

Simple scalar fields on candidates — RLS/grants from migration 0003 already cover the whole
table, no RLS changes needed here (same reasoning as Phase 6's projects.role_brief column-add).

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidates", sa.Column("interview_scheduled_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("candidates", sa.Column("prescreen_outcome", sa.String(20), nullable=True))
    op.add_column("candidates", sa.Column("prescreen_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "prescreen_notes")
    op.drop_column("candidates", "prescreen_outcome")
    op.drop_column("candidates", "interview_scheduled_at")
