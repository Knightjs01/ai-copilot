"""passport_job_matches.dimension_breakdown -- a real, evidence-backed per-dimension match
breakdown (Role alignment / Industry experience / Functional experience / Seniority / Location /
Compensation), replacing nothing (strengths/gaps/summary are unchanged) but adding structured
detail for the recruiter Match tab. Not nullable, default '[]': old cached rows simply show no
breakdown until their next recompute, same "recompute on demand, never serve stale AI output
silently" discipline every other field on this table already follows.

Revision ID: 0053
Revises: 0052
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0053"
down_revision: str | None = "0052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "passport_job_matches",
        sa.Column(
            "dimension_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("passport_job_matches", "dimension_breakdown")
