"""Employer Access Gate: removes public self-service company signup, replacing it with a
request -> Phantom-staff-review -> approve -> provision flow.

Adds two new tables: platform_admins (a wholly new principal type -- Phantom staff, deliberately
not a `users` row since users.company_id is NOT nullable and a platform admin belongs to no
tenant) and company_access_requests (the request queue). Adds companies.status
(approved/suspended) -- every existing company defaults to approved, so nothing already-live is
disrupted. No RLS on either new table -- neither is tenant-owned data, same reasoning as
saved_shadow_jobs/job_alerts; explicit GRANT instead.

Seeds exactly one bootstrap platform_admins row with a placeholder password -- disclosed once
outside version control, meant to be rotated immediately. Platform-admin self-service password
change doesn't exist yet (a stated Phase 1 limitation, see platform_admin/__init__.py).

Revision ID: 0040
Revises: 0039
Create Date: 2026-08-25

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.modules.auth.security import hash_password

revision: str = "0040"
down_revision: str | None = "0039"
branch_labels = None
depends_on = None

_BOOTSTRAP_ADMIN_EMAIL = "samuel@stormtalent.co.uk"
_BOOTSTRAP_ADMIN_FULL_NAME = "Samuel"
# Disclosed once, in chat, immediately after this migration ran -- rotate as soon as proper
# platform-admin account management exists. Never a real long-lived credential.
_BOOTSTRAP_ADMIN_PASSWORD = "UFk-sS0NltqqNZK2oZs_kheB"


def upgrade() -> None:
    op.create_table(
        "platform_admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_platform_admins_email", "platform_admins", ["email"], unique=True)

    op.create_table(
        "company_access_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("job_title", sa.String(255), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("work_email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "reviewed_by_admin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admins.id"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_company_access_requests_work_email",
        "company_access_requests",
        ["work_email"],
        unique=True,
    )

    op.add_column(
        "companies",
        sa.Column("status", sa.String(20), nullable=False, server_default="approved"),
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON platform_admins TO app_runtime, app_auth")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON company_access_requests TO app_runtime, app_auth"
    )

    platform_admins_table = sa.table(
        "platform_admins",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("email", sa.String),
        sa.column("hashed_password", sa.String),
        sa.column("full_name", sa.String),
    )
    op.bulk_insert(
        platform_admins_table,
        [
            {
                "id": uuid.uuid4(),
                "email": _BOOTSTRAP_ADMIN_EMAIL,
                "hashed_password": hash_password(_BOOTSTRAP_ADMIN_PASSWORD),
                "full_name": _BOOTSTRAP_ADMIN_FULL_NAME,
            }
        ],
    )


def downgrade() -> None:
    op.drop_column("companies", "status")
    op.drop_table("company_access_requests")
    op.drop_table("platform_admins")
