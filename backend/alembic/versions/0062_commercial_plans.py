"""Commercial Phase 1: a static Core/Growth/Scale plan catalog, two new columns on companies
(commercial_plan_id, active_role_limit_override), and a new commercial.manage platform-admin
permission granted to Super Admin + Platform Admin.

commercial_plans has no company_id and gets no RLS -- same "single-tenant-global data" reasoning
already applied to permissions/roles (migration 0001) and the platform_admin_* catalog tables
(migration 0059): there's one plan catalog, not one per company.

Every existing company is backfilled onto Core -- safe because this is pre-launch data with no
real billing/paying customers yet; nothing about how an existing company works today changes,
they just now have a real plan row instead of none. active_role_limit_override stays NULL for
everyone, so Core's own 5-role limit is what takes effect immediately -- see
commercial/service.py's docstring on why that's not a behavior regression for any company
currently running 5 or fewer active projects (the only shape of company that exists right now).

Revision ID: 0062
Revises: 0061
Create Date: 2026-08-28

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0062"
down_revision: str | None = "0061"
branch_labels = None
depends_on = None

_PLANS = [
    {"code": "core", "name": "Phantom Core", "monthly": 29900, "annual": 299000, "limit": 5},
    {"code": "growth", "name": "Phantom Growth", "monthly": 59900, "annual": 599000, "limit": 10},
    {"code": "scale", "name": "Phantom Scale", "monthly": 99900, "annual": 999000, "limit": None},
]

_COMMERCIAL_MANAGE_CODE = "commercial.manage"
_COMMERCIAL_MANAGE_DESCRIPTION = (
    "Change a company commercial plan and active-role limit override"
)
_GRANTED_ROLES = ["Super Admin", "Platform Admin"]


def upgrade() -> None:
    op.create_table(
        "commercial_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("monthly_price_pence", sa.Integer(), nullable=False),
        sa.Column("annual_price_pence", sa.Integer(), nullable=False),
        sa.Column("active_role_limit", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_commercial_plans_code", "commercial_plans", ["code"], unique=True)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON commercial_plans TO app_runtime, app_auth")

    plans_table = sa.table(
        "commercial_plans",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("monthly_price_pence", sa.Integer),
        sa.column("annual_price_pence", sa.Integer),
        sa.column("active_role_limit", sa.Integer),
    )
    plan_ids = {plan["code"]: uuid.uuid4() for plan in _PLANS}
    op.bulk_insert(
        plans_table,
        [
            {
                "id": plan_ids[plan["code"]],
                "code": plan["code"],
                "name": plan["name"],
                "monthly_price_pence": plan["monthly"],
                "annual_price_pence": plan["annual"],
                "active_role_limit": plan["limit"],
            }
            for plan in _PLANS
        ],
    )

    op.add_column(
        "companies",
        sa.Column(
            "commercial_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("commercial_plans.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "companies", sa.Column("active_role_limit_override", sa.Integer(), nullable=True)
    )

    op.execute(
        f"UPDATE companies SET commercial_plan_id = '{plan_ids['core']}'::uuid "
        "WHERE commercial_plan_id IS NULL"
    )

    # --- New platform-admin permission, granted to Super Admin + Platform Admin ------------------
    permission_id = uuid.uuid4()
    op.execute(
        f"""
        INSERT INTO platform_admin_permissions (id, code, description)
        VALUES ('{permission_id}'::uuid, '{_COMMERCIAL_MANAGE_CODE}',
                '{_COMMERCIAL_MANAGE_DESCRIPTION}')
        """
    )
    for role_name in _GRANTED_ROLES:
        op.execute(
            f"""
            INSERT INTO platform_admin_role_permissions (role_id, permission_id)
            SELECT r.id, '{permission_id}'::uuid
            FROM platform_admin_roles r
            WHERE r.name = '{role_name}'
            ON CONFLICT DO NOTHING
            """
        )


def downgrade() -> None:
    op.execute(
        f"DELETE FROM platform_admin_role_permissions WHERE permission_id IN "
        f"(SELECT id FROM platform_admin_permissions WHERE code = '{_COMMERCIAL_MANAGE_CODE}')"
    )
    op.execute(
        f"DELETE FROM platform_admin_permissions WHERE code = '{_COMMERCIAL_MANAGE_CODE}'"
    )
    op.drop_column("companies", "active_role_limit_override")
    op.drop_column("companies", "commercial_plan_id")
    op.drop_index("ix_commercial_plans_code", table_name="commercial_plans")
    op.drop_table("commercial_plans")
