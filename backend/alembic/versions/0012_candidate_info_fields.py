"""Candidate Info tab fields: current_employer, current_title, location, notice_period

Simple scalar column-adds — RLS/grants from migration 0003 already cover the whole table, same
reasoning as 0008/0010's column-adds.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-06

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("current_employer", sa.String(255), nullable=True))
    op.add_column("candidates", sa.Column("current_title", sa.String(255), nullable=True))
    op.add_column("candidates", sa.Column("location", sa.String(255), nullable=True))
    op.add_column("candidates", sa.Column("notice_period", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "notice_period")
    op.drop_column("candidates", "location")
    op.drop_column("candidates", "current_title")
    op.drop_column("candidates", "current_employer")
