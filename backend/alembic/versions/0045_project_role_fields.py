"""Adds seniority/location/salary_min/salary_max columns to projects -- AI Role Intake (ATS
redesign roadmap item 2). Mirrors ShadowJob's exact existing field types for these four columns
(shadow_jobs/models.py) for consistency across the codebase. Deliberately not adding
employment_type/remote_preference -- the master prompt's explicit ask was "Role, Seniority,
Location, Salary" only (Role = Project.title, already exists).

Nullable, no backfill -- existing projects simply show nothing for these fields until a
recruiter uploads a JD or fills them in manually, same honest no-fabricated-backfill discipline
every prior migration in this codebase follows.

Revision ID: 0045
Revises: 0044
Create Date: 2026-08-21

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0045"
down_revision: str | None = "0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("seniority", sa.String(100), nullable=True))
    op.add_column("projects", sa.Column("location", sa.String(255), nullable=True))
    op.add_column("projects", sa.Column("salary_min", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("salary_max", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "salary_max")
    op.drop_column("projects", "salary_min")
    op.drop_column("projects", "location")
    op.drop_column("projects", "seniority")
