"""Security: WebAuthn/passkey credential storage for both principals — see
app/core/webauthn.py. webauthn_credentials gets the standard tenant-isolation RLS treatment
(company_id denormalized from the owning user, same as mfa_backup_codes in migration 0022).
candidate_webauthn_credentials gets no RLS, matching every other candidate_auth table (see
migration 0016's docstring) — candidates have no company_id to scope a policy on.

Revision ID: 0027
Revises: 0026
Create Date: 2026-08-12

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webauthn_credentials",
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
        sa.Column("credential_id", sa.String(512), nullable=False, unique=True),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("device_name", sa.String(255), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_webauthn_credentials_user_id", "webauthn_credentials", ["user_id"])
    op.create_index("ix_webauthn_credentials_company_id", "webauthn_credentials", ["company_id"])
    op.create_index(
        "ix_webauthn_credentials_credential_id",
        "webauthn_credentials",
        ["credential_id"],
        unique=True,
    )

    op.execute("ALTER TABLE webauthn_credentials ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE webauthn_credentials FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_webauthn_credentials ON webauthn_credentials
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON webauthn_credentials TO app_runtime")
    # app_auth needs this too — the authentication-verify ceremony runs pre-auth (no company
    # context established yet), same reasoning as mfa_backup_codes in migration 0022.
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON webauthn_credentials TO app_auth")

    op.create_table(
        "candidate_webauthn_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column("credential_id", sa.String(512), nullable=False, unique=True),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("device_name", sa.String(255), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_candidate_webauthn_credentials_candidate_user_id",
        "candidate_webauthn_credentials",
        ["candidate_user_id"],
    )
    op.create_index(
        "ix_candidate_webauthn_credentials_credential_id",
        "candidate_webauthn_credentials",
        ["credential_id"],
        unique=True,
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON candidate_webauthn_credentials "
        "TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.drop_table("candidate_webauthn_credentials")
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_webauthn_credentials ON webauthn_credentials"
    )
    op.execute("ALTER TABLE webauthn_credentials NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE webauthn_credentials DISABLE ROW LEVEL SECURITY")
    op.drop_table("webauthn_credentials")
