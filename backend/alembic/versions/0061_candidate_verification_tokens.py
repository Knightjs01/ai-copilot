"""candidate_verification_tokens: real email verification for candidates.

Candidates have had an unused is_email_verified column since the very first Shadow migration
(0016) but no way to ever set it -- no verification email, no verify endpoint, nothing enforced.
This adds the token table backing a real verify-email flow, mirroring auth.models
.VerificationToken's shape but single-purpose (candidates only need this for one thing today, see
the model's own docstring) rather than a generic purpose-keyed table.

No RLS -- candidates aren't tenant-owned data, same reasoning as every other candidate_auth table.

Revision ID: 0061
Revises: 0060
Create Date: 2026-08-28

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0061"
down_revision: str | None = "0060"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_candidate_verification_tokens_candidate_user_id",
        "candidate_verification_tokens",
        ["candidate_user_id"],
    )
    op.create_index(
        "ix_candidate_verification_tokens_token_hash",
        "candidate_verification_tokens",
        ["token_hash"],
        unique=True,
    )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON candidate_verification_tokens "
        "TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.drop_table("candidate_verification_tokens")
