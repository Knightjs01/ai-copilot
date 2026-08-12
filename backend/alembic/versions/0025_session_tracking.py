"""Security: session/device tracking on refresh tokens — the foundation for an Active Sessions
view (list logged-in devices, revoke one remotely). No new tables: a refresh token row already
is a session, one row per device/browser; this just records what device it was issued to and
when it was last used.

Revision ID: 0025
Revises: 0024
Create Date: 2026-08-12

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("refresh_tokens", "candidate_refresh_tokens"):
        op.add_column(table, sa.Column("user_agent", sa.String(500), nullable=True))
        op.add_column(table, sa.Column("ip_address", sa.String(45), nullable=True))
        op.add_column(table, sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))
        # Backfill existing rows so last_used_at is never NULL going forward — application code
        # always sets it at issuance, this only covers rows that predate the column.
        op.execute(
            f"UPDATE {table} SET last_used_at = created_at WHERE last_used_at IS NULL"
        )  # noqa: S608


def downgrade() -> None:
    for table in ("refresh_tokens", "candidate_refresh_tokens"):
        op.drop_column(table, "last_used_at")
        op.drop_column(table, "ip_address")
        op.drop_column(table, "user_agent")
