"""Security: close RLS coverage gap on roles, role_permissions, user_roles, audit_logs

Every other tenant-owned table in this schema has a Postgres RLS policy backstopping its
company_id filtering. These four were missed — company_id (or, for the two join tables, a path
to it via roles) is currently enforced only by application code (repository WHERE clauses), the
exact "just app-level filtering" pattern this schema otherwise deliberately avoids. If a future
query ever forgot the filter, nothing at the database level would catch it.

permissions is deliberately excluded — it's a global, non-tenant-owned catalog table (no
company_id column at all), shared read-only reference data across every company.

Safe for the pre-auth flows (signup/login/etc, app_auth role, BYPASSRLS) since those ignore RLS
entirely regardless of app.current_company_id being set; safe for authenticated flows (app_runtime)
since they already query these tables scoped to the same company_id RLS now enforces.

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-12

"""

from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels = None
depends_on = None

_DIRECT_TABLES = ["roles", "audit_logs"]


def upgrade() -> None:
    for table in _DIRECT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (company_id = current_setting('app.current_company_id', true)::uuid)
            """
        )

    # role_permissions and user_roles are pure join tables with no company_id column of their
    # own — scope them via a subquery through roles, the same company_id every other policy in
    # this migration checks directly.
    op.execute("ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE role_permissions FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_role_permissions ON role_permissions
        USING (
            role_id IN (
                SELECT id FROM roles
                WHERE company_id = current_setting('app.current_company_id', true)::uuid
            )
        )
        """
    )

    op.execute("ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_roles FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_user_roles ON user_roles
        USING (
            role_id IN (
                SELECT id FROM roles
                WHERE company_id = current_setting('app.current_company_id', true)::uuid
            )
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_user_roles ON user_roles")
    op.execute("ALTER TABLE user_roles NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_roles DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_role_permissions ON role_permissions")
    op.execute("ALTER TABLE role_permissions NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE role_permissions DISABLE ROW LEVEL SECURITY")

    for table in _DIRECT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
