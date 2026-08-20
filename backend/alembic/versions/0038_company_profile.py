"""Company profile: adds description/culture/benefits/size/industry/is_profile_public to
companies (all nullable/default-empty/default-false -- nothing changes for any existing company
until they explicitly opt in and fill fields in). is_profile_public gates only whether a public
/companies/{slug} profile page exists -- job board listings always show the company name
regardless of this flag (see shadow_jobs/schemas.py's ShadowJobBoardListing docstring), so this
is purely additive.

No new permission -- reuses the existing, previously-unused company.manage_settings permission
(seeded in 0001, granted to Owner+Admin, gated on zero endpoints until this migration's PATCH
/companies/me route).

Revision ID: 0038
Revises: 0037
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0038"
down_revision: str | None = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("culture", sa.Text(), nullable=True))
    op.add_column(
        "companies",
        sa.Column(
            "benefits", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"
        ),
    )
    op.add_column("companies", sa.Column("size", sa.String(20), nullable=True))
    op.add_column(
        "companies",
        sa.Column(
            "industry", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "companies",
        sa.Column("is_profile_public", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("companies", "is_profile_public")
    op.drop_column("companies", "industry")
    op.drop_column("companies", "size")
    op.drop_column("companies", "benefits")
    op.drop_column("companies", "culture")
    op.drop_column("companies", "description")
