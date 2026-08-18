"""Drops passport_personal_info.address_encrypted -- the Passport wizard's Personal Identity
step no longer collects an address (replaced by the candidate's already-known login email and
the relocated location field). Confirmed via grep that no other module reads this column.

Revision ID: 0032
Revises: 0031
Create Date: 2026-08-18

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("passport_personal_info", "address_encrypted")


def downgrade() -> None:
    op.add_column(
        "passport_personal_info", sa.Column("address_encrypted", sa.Text(), nullable=True)
    )
