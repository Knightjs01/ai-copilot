"""Adds industry/years_experience columns to intelligence_packs -- ATS-side Fit Intelligence
extension (Phantom ATS UX redesign, Phase 1). Mirrors the columns PhantomPassport already has
(years_experience: int | None, industries: list -- here a single scalar industry: str | None,
matching this module's existing "flat scalar fields" convention rather than a JSONB list).

Nullable, no backfill -- existing packs simply show nothing for these fields until regenerated,
same honest no-fabricated-backfill discipline every prior migration in this codebase follows.

Revision ID: 0044
Revises: 0043
Create Date: 2026-08-20

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0044"
down_revision: str | None = "0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("intelligence_packs", sa.Column("industry", sa.String(255), nullable=True))
    op.add_column("intelligence_packs", sa.Column("years_experience", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("intelligence_packs", "years_experience")
    op.drop_column("intelligence_packs", "industry")
