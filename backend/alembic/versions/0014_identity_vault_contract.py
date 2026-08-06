"""Candidate Identity Vault (contract): drop the now-unused PII columns from candidates.

Second half of the 0013/0014 expand/contract pair — by this point every candidate row has been
backfilled into candidate_identity_vaults (0013) and the application code no longer reads or
writes full_name/email/phone/location/current_employer/current_title on Candidate at all, so
these columns are purely inert. Kept as a separate revision so there was an independent rollback
point after the backfill but before this irreversible step.

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-06

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("candidates", "full_name")
    op.drop_column("candidates", "email")
    op.drop_column("candidates", "phone")
    op.drop_column("candidates", "location")
    op.drop_column("candidates", "current_employer")
    op.drop_column("candidates", "current_title")


def downgrade() -> None:
    # Schema-only rollback — the original PII values are gone with 0013's forward path, since
    # they only ever lived in the encrypted vault after that point. Re-adding these columns nulls
    # them out; they are NOT repopulated from candidate_identity_vaults.
    op.add_column("candidates", sa.Column("full_name", sa.String(255), nullable=True))
    op.add_column("candidates", sa.Column("email", sa.String(320), nullable=True))
    op.add_column("candidates", sa.Column("phone", sa.String(50), nullable=True))
    op.add_column("candidates", sa.Column("location", sa.String(255), nullable=True))
    op.add_column("candidates", sa.Column("current_employer", sa.String(255), nullable=True))
    op.add_column("candidates", sa.Column("current_title", sa.String(255), nullable=True))
