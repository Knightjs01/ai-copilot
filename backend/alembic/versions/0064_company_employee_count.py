"""Adds Company.employee_count -- a precise, company-entered headcount for the internal-only
"team size" stat on the company's own profile page. Distinct from the existing `size` column (a
coarse public band like "51-200"): using UserRepository.count_by_company (Phantom Hire login
count) for "team size" was flagged as wrong before shipping -- a company's real employee count and
its number of platform users are unrelated numbers.

Revision ID: 0064
Revises: 0063
Create Date: 2026-08-28

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0064"
down_revision: str | None = "0063"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("employee_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "employee_count")
