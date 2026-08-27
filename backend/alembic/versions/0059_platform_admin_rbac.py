"""Platform-admin RBAC: 5 roles (Super Admin/Platform Admin/Reviewer/Support Admin/Analytics),
a 7-code permission catalog, and their grants -- mirrors the company-user RBAC shape (roles/
permissions/role_permissions/user_roles from migration 0001) for the platform_admins principal.

Unlike company roles, these are NOT per-tenant -- there's exactly one platform, not many
companies each needing their own copy of "Super Admin" -- so platform_admin_roles.name is
globally unique and every role/permission/grant is static seed data inserted once here, not a
runtime seeding function triggered per company. No RLS on any of the 4 new tables, same reasoning
roles/permissions/role_permissions already have none (single-tenant-global data, migration 0001).

Also assigns the existing samuel@stormtalent.co.uk platform admin (seeded by migration 0040) the
Super Admin role -- without this, the real admin is locked out of admins.manage/danger_zone.purge
the moment this ships.

Revision ID: 0059
Revises: 0058
Create Date: 2026-08-27

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0059"
down_revision: str | None = "0058"
branch_labels = None
depends_on = None

_ROLES = ["Super Admin", "Platform Admin", "Reviewer", "Support Admin", "Analytics"]

_PERMISSIONS = [
    ("admins.manage", "Create platform-admin accounts and assign roles"),
    (
        "companies.manage",
        "Approve/reject access requests, suspend/reactivate companies, review company profiles",
    ),
    ("companies.view", "View the companies and access-requests lists"),
    ("jobs.review", "Approve or reject a job submitted for Shadow review"),
    ("jobs.view", "View the job-review queue"),
    ("danger_zone.purge", "Purge all tenant data platform-wide"),
    ("audit.view", "View the platform-admin activity log"),
]

_ALL_CODES = [code for code, _ in _PERMISSIONS]

_ROLE_GRANTS: dict[str, list[str]] = {
    "Super Admin": _ALL_CODES,
    "Platform Admin": [
        "companies.manage",
        "companies.view",
        "jobs.review",
        "jobs.view",
        "audit.view",
    ],
    "Reviewer": ["companies.view", "jobs.review", "jobs.view", "audit.view"],
    "Support Admin": ["companies.view", "audit.view"],
    "Analytics": ["companies.view", "jobs.view", "audit.view"],
}

_BOOTSTRAP_ADMIN_EMAIL = "samuel@stormtalent.co.uk"


def upgrade() -> None:
    op.create_table(
        "platform_admin_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "platform_admin_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=False),
    )
    op.create_index(
        "ix_platform_admin_permissions_code", "platform_admin_permissions", ["code"], unique=True
    )

    op.create_table(
        "platform_admin_role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admin_roles.id"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admin_permissions.id"),
            primary_key=True,
        ),
    )

    op.create_table(
        "platform_admin_role_assignments",
        sa.Column(
            "admin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admins.id"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admin_roles.id"),
            primary_key=True,
        ),
    )

    for table in (
        "platform_admin_roles",
        "platform_admin_permissions",
        "platform_admin_role_permissions",
        "platform_admin_role_assignments",
    ):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_runtime, app_auth")

    # --- Seed roles ------------------------------------------------------------------------
    roles_table = sa.table(
        "platform_admin_roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("is_system", sa.Boolean),
    )
    role_ids = {name: uuid.uuid4() for name in _ROLES}
    op.bulk_insert(
        roles_table,
        [{"id": role_ids[name], "name": name, "is_system": True} for name in _ROLES],
    )

    # --- Seed permission catalog -------------------------------------------------------------
    permissions_table = sa.table(
        "platform_admin_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    permission_ids = {code: uuid.uuid4() for code, _ in _PERMISSIONS}
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[code], "code": code, "description": desc}
            for code, desc in _PERMISSIONS
        ],
    )

    # --- Grant matrix --------------------------------------------------------------------------
    role_permissions_table = sa.table(
        "platform_admin_role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    grants = [
        {"role_id": role_ids[role_name], "permission_id": permission_ids[code]}
        for role_name, codes in _ROLE_GRANTS.items()
        for code in codes
    ]
    op.bulk_insert(role_permissions_table, grants)

    # --- Bootstrap: samuel becomes Super Admin ------------------------------------------------
    op.execute(
        f"""
        INSERT INTO platform_admin_role_assignments (admin_id, role_id)
        SELECT pa.id, '{role_ids["Super Admin"]}'::uuid
        FROM platform_admins pa
        WHERE pa.email = '{_BOOTSTRAP_ADMIN_EMAIL}'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("platform_admin_role_assignments")
    op.drop_table("platform_admin_role_permissions")
    op.drop_table("platform_admin_permissions")
    op.drop_table("platform_admin_roles")
