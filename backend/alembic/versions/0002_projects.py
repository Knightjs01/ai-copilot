"""Phase 2: projects table, tenant-isolation RLS, projects.* permissions

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-05

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels = None
depends_on = None

# Fixed at authoring time, same reasoning as 0001's permission seed — deterministic, no
# pgcrypto dependency.
_NEW_PERMISSIONS = [
    (uuid.uuid4(), "projects.create", "Create hiring projects"),
    (uuid.uuid4(), "projects.view", "View hiring projects"),
    (uuid.uuid4(), "projects.update", "Update hiring projects"),
    (uuid.uuid4(), "projects.delete", "Archive hiring projects"),
]

# Owner gets everything (matches ALL_PERMISSIONS in app/modules/auth/permissions.py at the time
# this migration was written); Admin gets the same as Owner for projects; Member gets view only.
_OWNER_AND_ADMIN_CODES = ["projects.create", "projects.view", "projects.update", "projects.delete"]
_MEMBER_CODES = ["projects.view"]


def upgrade() -> None:
    # Must run before creating any new tables: Phase 1's ALTER DEFAULT PRIVILEGES loop granted
    # app_auth (pre-authentication only) access to every future table too, which isn't
    # least-privilege — app_auth only ever needs the 3 auth tables it already has. This doesn't
    # touch those existing grants, only the default applied to tables created after this point.
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM app_auth")

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "hiring_manager_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_projects_company_id", "projects", ["company_id"])

    # Same tenant-isolation treatment as `users` in 0001.
    op.execute("ALTER TABLE projects ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE projects FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_projects ON projects
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    # Explicit grant rather than relying solely on the default-privileges inheritance from 0001 —
    # cheap belt-and-braces given how easy this class of bug is to get silently wrong.
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON projects TO app_runtime")

    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        permissions_table,
        [{"id": pid, "code": code, "description": desc} for pid, code, desc in _NEW_PERMISSIONS],
    )

    # Role-seeding only runs once, at signup — existing companies' Owner/Admin/Member roles need
    # a catch-up grant for permissions added after they were created. This pattern repeats for
    # every future permission-gated feature.
    owner_admin_codes = ", ".join(f"'{code}'" for code in _OWNER_AND_ADMIN_CODES)
    member_codes = ", ".join(f"'{code}'" for code in _MEMBER_CODES)

    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name IN ('Owner', 'Admin') AND p.code IN ({owner_admin_codes})
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'Member' AND p.code IN ({member_codes})
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_projects ON projects")
    op.execute("ALTER TABLE projects NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE projects DISABLE ROW LEVEL SECURITY")
    op.drop_table("projects")

    owner_admin_codes = ", ".join(f"'{code}'" for code in _OWNER_AND_ADMIN_CODES)
    member_codes = ", ".join(f"'{code}'" for code in _MEMBER_CODES)
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ({owner_admin_codes}))
        """
    )
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ({member_codes}))
        """
    )
    op.execute(f"DELETE FROM permissions WHERE code IN ({owner_admin_codes})")

    # Deliberately not restoring app_auth's default-privileges grant on future tables — that was
    # a security fix, not something a schema rollback should undo.
