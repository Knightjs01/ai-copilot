"""Intelligence pack: highlights column

Simple JSONB column-add — RLS/grants from migration 0005 already cover the whole table, same
reasoning as 0008/0010's column-adds.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-06

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "intelligence_packs",
        sa.Column("highlights", postgresql.JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("intelligence_packs", "highlights")
