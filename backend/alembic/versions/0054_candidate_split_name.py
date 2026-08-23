"""candidate_users: split full_name into first_name/last_name.

Single migration, not an expand/contract pair -- backend and frontend for this table are
deployed together as one app (no independently-versioned client holding onto the old shape), so
there's no window where a live caller could still expect full_name after this ships. Backfills
existing rows by splitting on the first whitespace (first word -> first_name, everything else ->
last_name, NULL if there was only one word) -- the same "first word / rest" heuristic already
used client-side in the Passport wizard's own name-splitting fallback.

Revision ID: 0054
Revises: 0053
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0054"
down_revision: str | None = "0053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidate_users", sa.Column("first_name", sa.String(255), nullable=True))
    op.add_column("candidate_users", sa.Column("last_name", sa.String(255), nullable=True))
    op.execute(
        """
        UPDATE candidate_users SET
            first_name = split_part(full_name, ' ', 1),
            last_name = NULLIF(btrim(substr(full_name, length(split_part(full_name, ' ', 1)) + 1)), '')
        """
    )
    op.alter_column("candidate_users", "first_name", nullable=False)
    op.drop_column("candidate_users", "full_name")


def downgrade() -> None:
    op.add_column("candidate_users", sa.Column("full_name", sa.String(255), nullable=True))
    op.execute(
        """
        UPDATE candidate_users SET
            full_name = btrim(first_name || ' ' || COALESCE(last_name, ''))
        """
    )
    op.alter_column("candidate_users", "full_name", nullable=False)
    op.drop_column("candidate_users", "last_name")
    op.drop_column("candidate_users", "first_name")
