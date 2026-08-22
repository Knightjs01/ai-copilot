"""shadow_applications.viewed_at -- tracks whether a recruiter has opened this applicant's card
yet, powering a "New application" badge on the Kanban/applicant-list surfaces. Nullable; NULL
means genuinely unviewed. Existing rows are backfilled to their own created_at so applications
that were submitted before this column existed don't retroactively show as "new" -- only
applications submitted after this migration start out unviewed.

Revision ID: 0050
Revises: 0049
Create Date: 2026-08-22

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0050"
down_revision: str | None = "0049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shadow_applications",
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE shadow_applications SET viewed_at = created_at")


def downgrade() -> None:
    op.drop_column("shadow_applications", "viewed_at")
