"""Security: mfa_backup_codes table — the only account recovery path if a user loses their
authenticator app. Same RLS/grant template as every other tenant-owned table in this schema.

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-12

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mfa_backup_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_mfa_backup_codes_user_id", "mfa_backup_codes", ["user_id"])
    op.create_index("ix_mfa_backup_codes_company_id", "mfa_backup_codes", ["company_id"])
    op.create_index("ix_mfa_backup_codes_code_hash", "mfa_backup_codes", ["code_hash"], unique=True)

    op.execute("ALTER TABLE mfa_backup_codes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE mfa_backup_codes FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_mfa_backup_codes ON mfa_backup_codes
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON mfa_backup_codes TO app_runtime")
    # app_auth needs this too — verify_mfa_and_login runs on the pre-auth get_db session (the
    # user hasn't received a company-scoped access token yet at that point in the login flow).
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON mfa_backup_codes TO app_auth")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_mfa_backup_codes ON mfa_backup_codes")
    op.execute("ALTER TABLE mfa_backup_codes NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE mfa_backup_codes DISABLE ROW LEVEL SECURITY")
    op.drop_table("mfa_backup_codes")
