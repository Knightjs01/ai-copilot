"""Company Profile Visual Rebuild: adds tagline/website/founded_year/headquarters (plain facts),
is_verified_employer (a real, admin-only-settable verification flag -- distinct from the existing
is_verified_domain heuristic), and values/looking_for/hiring_highlights (JSONB content lists,
same storage pattern as the existing benefits/industry columns).

All additive and defaulted/nullable -- no existing company's behavior changes until it (or an
admin) explicitly sets one of these.

Revision ID: 0063
Revises: 0062
Create Date: 2026-08-28

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0063"
down_revision: str | None = "0062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("tagline", sa.String(255), nullable=True))
    op.add_column("companies", sa.Column("website", sa.String(255), nullable=True))
    op.add_column("companies", sa.Column("founded_year", sa.Integer(), nullable=True))
    op.add_column("companies", sa.Column("headquarters", sa.String(255), nullable=True))
    op.add_column(
        "companies",
        sa.Column("is_verified_employer", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "companies",
        sa.Column(
            "values", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "looking_for",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "hiring_highlights",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("companies", "hiring_highlights")
    op.drop_column("companies", "looking_for")
    op.drop_column("companies", "values")
    op.drop_column("companies", "is_verified_employer")
    op.drop_column("companies", "headquarters")
    op.drop_column("companies", "founded_year")
    op.drop_column("companies", "website")
    op.drop_column("companies", "tagline")
