"""Anonymous Candidate Discovery Phase 4: talent_pool_grants.pool_name -- a company-only
organizational label over an already-GRANTED row. No new entity table: a "pool" is just "every
granted row sharing this string", mirroring SavedShadowJob.collection_name's exact pattern
(additive nullable column, no dedicated pool-management table) rather than a new TalentPool
entity with its own CRUD lifecycle. Never surfaced to the candidate, never touched by the
request/respond consent flow.

Revision ID: 0069
Revises: 0068
Create Date: 2026-08-30

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0069"
down_revision: str | None = "0068"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "talent_pool_grants", sa.Column("pool_name", sa.String(100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("talent_pool_grants", "pool_name")
