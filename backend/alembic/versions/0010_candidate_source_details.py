"""Candidate source details: expected_salary, agency_name

Simple scalar fields on candidates — RLS/grants from migration 0003 already cover the whole
table, same reasoning as 0008's column-add.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-06

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("expected_salary", sa.Integer(), nullable=True))
    op.add_column("candidates", sa.Column("agency_name", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "agency_name")
    op.drop_column("candidates", "expected_salary")
