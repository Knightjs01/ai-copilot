"""shadow_reveal_requests.company_viewed_at -- tracks whether the recruiter side has opened this
applicant's card since the candidate last responded (approved/declined) to a reveal request,
powering an "unseen reveal response" badge and a dashboard action item. Nullable; NULL means
genuinely unseen. Existing rows are backfilled to their own responded_at (when set) so reveal
responses that already happened before this column existed don't retroactively show as unseen --
only responses recorded after this migration start out unseen. Rows still pending have no
response yet, so they're left NULL either way (irrelevant until responded_at is set).

Revision ID: 0051
Revises: 0050
Create Date: 2026-08-22

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0051"
down_revision: str | None = "0050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shadow_reveal_requests",
        sa.Column("company_viewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE shadow_reveal_requests SET company_viewed_at = responded_at "
        "WHERE responded_at IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("shadow_reveal_requests", "company_viewed_at")
