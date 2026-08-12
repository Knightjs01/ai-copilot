"""Security: granular disclosure levels for identity_vault and shadow_reveal — both were binary
(full snapshot or nothing) before this. See app/core/disclosure.py.

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-12

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "identity_reveal_events",
        sa.Column(
            "disclosure_level", sa.String(20), nullable=False, server_default=sa.text("'full'")
        ),
    )
    # No server_default here — nullable/absent by design for pending/declined requests, only
    # ever set at the moment a candidate approves (see ShadowRevealRequestRepository.respond).
    op.add_column(
        "shadow_reveal_requests", sa.Column("disclosure_level", sa.String(20), nullable=True)
    )
    # Existing approved requests predate this column — backfill them to 'full' so their
    # already-granted disclosure doesn't silently narrow the next time it's viewed.
    op.execute(
        "UPDATE shadow_reveal_requests SET disclosure_level = 'full' WHERE status = 'approved'"
    )


def downgrade() -> None:
    op.drop_column("shadow_reveal_requests", "disclosure_level")
    op.drop_column("identity_reveal_events", "disclosure_level")
