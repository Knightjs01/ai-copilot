"""Phase 1: companies, users, RBAC, tokens, audit log, tenant-isolation RLS

Revision ID: 0001
Revises:
Create Date: 2026-08-05

"""

import os
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels = None
depends_on = None

# Fixed at authoring time (not gen_random_uuid()) so this migration is fully deterministic and
# doesn't depend on the pgcrypto extension being enabled — the app always generates ids
# client-side via the ORM, this seed data is the one exception.
_PERMISSIONS = [
    (uuid.uuid4(), "users.view", "View company users"),
    (uuid.uuid4(), "users.invite", "Invite new users to the company"),
    (uuid.uuid4(), "users.change_role", "Change another user's role"),
    (uuid.uuid4(), "users.remove", "Remove a user from the company"),
    (uuid.uuid4(), "company.manage_settings", "Manage company-level settings"),
]


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_companies_slug", "companies", ["slug"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("mfa_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("mfa_secret_encrypted", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_company_id", "users", ["company_id"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=False),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("company_id", "name", name="uq_roles_company_name"),
    )
    op.create_index("ix_roles_company_id", "roles", ["company_id"])

    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), primary_key=True
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permissions.id"),
            primary_key=True,
        ),
    )

    op.create_table(
        "user_roles",
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True
        ),
        sa.Column(
            "role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), primary_key=True
        ),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    op.create_table(
        "verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_verification_tokens_user_id", "verification_tokens", ["user_id"])
    op.create_index("ix_verification_tokens_purpose", "verification_tokens", ["purpose"])
    op.create_index("ix_verification_tokens_token_hash", "verification_tokens", ["token_hash"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_company_id", "audit_logs", ["company_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

    # Seed the permission catalog — the source of truth for codes/descriptions at runtime is
    # app.modules.auth.permissions.ALL_PERMISSIONS; this is a one-time historical snapshot.
    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        permissions_table,
        [{"id": pid, "code": code, "description": desc} for pid, code, desc in _PERMISSIONS],
    )

    # Tenant isolation: the actual enforcement mechanism, not just an app-level convention.
    # RLS already applies to any role other than the table owner, superusers, and BYPASSRLS
    # roles — FORCE is extra insurance so even an ad-hoc query run as the owning migration role
    # (copilot) can't accidentally read cross-tenant rows either.
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_users ON users
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    # The app must never connect as the Postgres bootstrap superuser (copilot) — superusers and
    # BYPASSRLS roles ignore row-level security unconditionally, which would make the policy
    # above silently inert. app_runtime is a genuinely restricted role for tenant-scoped runtime
    # queries; only migrations (which need real DDL privileges) connect as copilot.
    #
    # app_auth is a second, deliberately narrower exception: signup/login/refresh/password-reset/
    # email-verification/accept-invite all need to look a user up by email or by a random opaque
    # token *before* their company is known — that's inherently a cross-tenant lookup, which a
    # company_id-scoped RLS policy can never satisfy. app_auth gets BYPASSRLS so those specific,
    # narrowly-defined flows keep working; every other (tenant-scoped) query still goes through
    # app_runtime and is fully subject to the policy above. See app/db/session.get_db vs.
    # app/modules/auth/dependencies.get_tenant_db for which role each is used from.
    def _create_or_update_role(name: str, password_env_var: str, *, bypass_rls: bool) -> None:
        password = os.environ.get(password_env_var)
        if not password:
            raise RuntimeError(f"{password_env_var} must be set to run this migration")
        escaped_password = password.replace("'", "''")
        rls_attr = "BYPASSRLS" if bypass_rls else "NOBYPASSRLS"

        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{name}') THEN
                    CREATE ROLE {name} LOGIN PASSWORD '{escaped_password}' {rls_attr};
                ELSE
                    ALTER ROLE {name} LOGIN PASSWORD '{escaped_password}' {rls_attr};
                END IF;
            END
            $$
            """
        )
        op.execute(f"GRANT USAGE ON SCHEMA public TO {name}")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {name}")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {name}"
        )

    _create_or_update_role("app_runtime", "APP_DB_PASSWORD", bypass_rls=False)
    _create_or_update_role("app_auth", "AUTH_DB_PASSWORD", bypass_rls=True)


def downgrade() -> None:
    for name in ("app_runtime", "app_auth"):
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM {name}")
        op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {name}")
        op.execute(f"REVOKE USAGE ON SCHEMA public FROM {name}")
        op.execute(f"DROP ROLE IF EXISTS {name}")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")
    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")

    op.drop_table("audit_logs")
    op.drop_table("verification_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
    op.drop_table("users")
    op.drop_table("companies")
