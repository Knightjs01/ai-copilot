"""platform_admin_refresh_tokens: real session persistence for the platform-admin portal.

Mirrors refresh_tokens/candidate_refresh_tokens' exact shape and rotation semantics. Platform
admin previously had no refresh token at all -- the access token lived in frontend memory only
and a session ended on every reload or after 15 minutes, with no way to renew it (see
platform_admin_api_client.ts's own prior comment). No RLS -- not tenant data, same reasoning as
platform_admins itself.

Revision ID: 0058
Revises: 0057
Create Date: 2026-08-27

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0058"
down_revision: str | None = "0057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_admin_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "admin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admins.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_platform_admin_refresh_tokens_admin_id",
        "platform_admin_refresh_tokens",
        ["admin_id"],
    )
    op.create_index(
        "ix_platform_admin_refresh_tokens_token_hash",
        "platform_admin_refresh_tokens",
        ["token_hash"],
        unique=True,
    )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON platform_admin_refresh_tokens "
        "TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.drop_table("platform_admin_refresh_tokens")
