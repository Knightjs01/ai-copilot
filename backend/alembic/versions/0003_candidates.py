"""Phase 3: candidates table, tenant-isolation RLS, candidates.* permissions

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-05

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels = None
depends_on = None

_NEW_PERMISSIONS = [
    (uuid.uuid4(), "candidates.create", "Add candidates"),
    (uuid.uuid4(), "candidates.view", "View candidates"),
    (uuid.uuid4(), "candidates.update", "Update candidates (including resume uploads)"),
    (uuid.uuid4(), "candidates.delete", "Archive candidates"),
]

_OWNER_AND_ADMIN_CODES = [
    "candidates.create",
    "candidates.view",
    "candidates.update",
    "candidates.delete",
]
_MEMBER_CODES = ["candidates.view"]


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="direct"),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("resume_file_key", sa.String(255), nullable=True),
        sa.Column("resume_original_filename", sa.String(255), nullable=True),
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
    op.create_index("ix_candidates_company_id", "candidates", ["company_id"])
    op.create_index("ix_candidates_project_id", "candidates", ["project_id"])

    # Same tenant-isolation treatment as `users`/`projects`.
    op.execute("ALTER TABLE candidates ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE candidates FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_candidates ON candidates
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    # Explicit grant, same belt-and-braces reasoning as 0002 — app_auth is NOT granted here
    # (its default-privileges access to future tables was revoked in 0002), so it should have
    # zero access to this table; see test_app_auth_role_has_no_grants_on_candidates.
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON candidates TO app_runtime")

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
    op.execute("DROP POLICY IF EXISTS tenant_isolation_candidates ON candidates")
    op.execute("ALTER TABLE candidates NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE candidates DISABLE ROW LEVEL SECURITY")
    op.drop_table("candidates")

    owner_admin_codes = ", ".join(f"'{code}'" for code in _OWNER_AND_ADMIN_CODES)
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ({owner_admin_codes}))
        """
    )
    op.execute(f"DELETE FROM permissions WHERE code IN ({owner_admin_codes})")
