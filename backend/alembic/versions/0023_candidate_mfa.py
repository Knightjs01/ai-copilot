"""Security: MFA parity for CandidateUser — TOTP + backup codes, mirroring migration 0022's
company-user feature. Deliberately no RLS on candidate_mfa_backup_codes, same reasoning as every
other candidate_auth table (see migration 0016's docstring): candidates have no company_id to
scope a tenant-isolation policy on, so authorization stays purely at the application layer.

Revision ID: 0023
Revises: 0022
Create Date: 2026-08-12

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_users",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "candidate_users", sa.Column("mfa_secret_encrypted", sa.String(255), nullable=True)
    )

    op.create_table(
        "candidate_mfa_backup_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_candidate_mfa_backup_codes_candidate_user_id",
        "candidate_mfa_backup_codes",
        ["candidate_user_id"],
    )
    op.create_index(
        "ix_candidate_mfa_backup_codes_code_hash",
        "candidate_mfa_backup_codes",
        ["code_hash"],
        unique=True,
    )

    # Explicit, not relying on ALTER DEFAULT PRIVILEGES alone — see migration 0016's comment for
    # why that's not been a safe assumption in this environment's history. app_auth needs this:
    # every candidate_auth route (including verify_mfa_and_login, pre-auth) runs on app_auth.
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON candidate_mfa_backup_codes TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.drop_table("candidate_mfa_backup_codes")
    op.drop_column("candidate_users", "mfa_secret_encrypted")
    op.drop_column("candidate_users", "mfa_enabled")
