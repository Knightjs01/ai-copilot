"""Talent Memory Phase 2: talent_pool_grants.source_project_id -- the column needed to know
which project a project_only grant was scoped to, so a new role linked to that same project can
be matched against it. Nullable, ON DELETE SET NULL, same treatment as
source_shadow_application_id (0046) -- a burned project must not break the FK, and a grant whose
project has gone null can honestly never match project_only again (there's no "this project"
left to scope to).

No backfill -- existing grants (all from Phase 1, before this column existed) simply can't match
project_only scope until re-requested. This is the honest default: no wrong-project matches are
possible from null data.

Revision ID: 0047
Revises: 0046
Create Date: 2026-08-22

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0047"
down_revision: str | None = "0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "talent_pool_grants",
        sa.Column(
            "source_project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_talent_pool_grants_source_project_id", "talent_pool_grants", ["source_project_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_talent_pool_grants_source_project_id", table_name="talent_pool_grants")
    op.drop_column("talent_pool_grants", "source_project_id")
