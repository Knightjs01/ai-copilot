"""Talent Memory Phase 3: passport_job_matches.candidate_notified_at -- tracks whether the
candidate has already been emailed about a given (passport_version, shadow_job) match, so a
recruiter re-running a Talent Pool search doesn't re-email the same candidate about the same
match. Nullable, no backfill (every existing match predates this notification flow, so nothing
should retroactively fire).

Revision ID: 0048
Revises: 0047
Create Date: 2026-08-22

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0048"
down_revision: str | None = "0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "passport_job_matches",
        sa.Column("candidate_notified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("passport_job_matches", "candidate_notified_at")
