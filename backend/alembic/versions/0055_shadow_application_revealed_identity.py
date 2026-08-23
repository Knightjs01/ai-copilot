"""shadow_applications: persist decrypted identity once revealed.

Once a company completes the existing step-up-gated "Reveal Identity" action for an application,
the decrypted name/email/phone get written here -- the single authoritative source every other
surface (Kanban, applicant list, workspace, Passport sidebar, messages, interviews) reads from
going forward, instead of each one needing its own step-up-gated decrypt. Populated exactly once,
by ShadowRevealService.get_revealed_identity on first successful reveal; nullable, no backfill
(nothing existing was ever decrypted this way before). Same protection tier as before -- this
table's grants are unchanged, and the write is still gated behind the exact same step-up +
approved-reveal-request checks that already exist -- just persisted instead of decrypt-on-demand.

Revision ID: 0055
Revises: 0054
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0055"
down_revision: str | None = "0054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shadow_applications", sa.Column("revealed_full_name", sa.String(255), nullable=True)
    )
    op.add_column(
        "shadow_applications", sa.Column("revealed_email", sa.String(320), nullable=True)
    )
    op.add_column(
        "shadow_applications", sa.Column("revealed_phone", sa.String(50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("shadow_applications", "revealed_phone")
    op.drop_column("shadow_applications", "revealed_email")
    op.drop_column("shadow_applications", "revealed_full_name")
