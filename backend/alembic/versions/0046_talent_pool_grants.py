"""Talent Memory Phase 1: talent_pool_grants table -- the permissioned Candidate <-> Company
relationship. One row per request cycle (mirrors shadow_reveal_requests' append-only shape).

A hard unique constraint on (candidate_user_id, company_id) would permanently block re-requesting
after a decline/withdrawal, so this uses a partial unique index instead, covering only the
non-terminal statuses (requested/granted) -- a fresh request is always possible once a prior one
has been declined or withdrawn.

Same dual-grant treatment as shadow_reveal_requests (0018): RLS by company_id for the company
side (app_runtime), explicit GRANT to app_auth too since the candidate views/responds to their
own requests through the app_auth connection, bypassing RLS, filtered explicitly by
candidate_user_id in application code.

New permissions talent_pool.request / talent_pool.view -- Owner (auto) + TA Admin + Recruiter get
both (day-to-day Shadow applicant work), Hiring Manager gets view only, Interviewer gets neither.

Revision ID: 0046
Revises: 0045
Create Date: 2026-08-22

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0046"
down_revision: str | None = "0045"
branch_labels = None
depends_on = None

_NEW_PERMISSIONS = [
    (
        uuid.uuid4(),
        "talent_pool.request",
        "Ask a Shadow applicant to be kept on file for future roles",
    ),
    (
        uuid.uuid4(),
        "talent_pool.view",
        "View candidates who have granted future-role Talent Pool access",
    ),
]
_REQUEST_AND_VIEW_CODES = ["talent_pool.request", "talent_pool.view"]
_VIEW_ONLY_CODES = ["talent_pool.view"]


def upgrade() -> None:
    op.create_table(
        "talent_pool_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "source_shadow_application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_role_title", sa.String(255), nullable=False),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("scope", sa.String(20), nullable=False, server_default="project_only"),
        sa.Column("status", sa.String(20), nullable=False, server_default="requested"),
        sa.Column("purpose", sa.String(50), nullable=False, server_default="future_role_matching"),
        sa.Column("lawful_basis", sa.String(20), nullable=False, server_default="consent"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_talent_pool_grants_candidate_user_id", "talent_pool_grants", ["candidate_user_id"]
    )
    op.create_index("ix_talent_pool_grants_company_id", "talent_pool_grants", ["company_id"])
    op.create_index(
        "uq_talent_pool_grants_active_pair",
        "talent_pool_grants",
        ["candidate_user_id", "company_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('requested', 'granted')"),
    )

    op.execute("ALTER TABLE talent_pool_grants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE talent_pool_grants FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_talent_pool_grants ON talent_pool_grants
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON talent_pool_grants TO app_runtime, app_auth"
    )

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

    request_and_view_codes = ", ".join(f"'{code}'" for code in _REQUEST_AND_VIEW_CODES)
    view_only_codes = ", ".join(f"'{code}'" for code in _VIEW_ONLY_CODES)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name IN ('Owner', 'TA Admin', 'Recruiter') AND p.code IN ({request_and_view_codes})
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'Hiring Manager' AND p.code IN ({view_only_codes})
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    all_codes = ", ".join(f"'{code}'" for code in _REQUEST_AND_VIEW_CODES)
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ({all_codes}))
        """
    )
    op.execute(f"DELETE FROM permissions WHERE code IN ({all_codes})")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_talent_pool_grants ON talent_pool_grants")
    op.execute("ALTER TABLE talent_pool_grants NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE talent_pool_grants DISABLE ROW LEVEL SECURITY")
    op.drop_index("uq_talent_pool_grants_active_pair", table_name="talent_pool_grants")
    op.drop_index("ix_talent_pool_grants_company_id", table_name="talent_pool_grants")
    op.drop_index("ix_talent_pool_grants_candidate_user_id", table_name="talent_pool_grants")
    op.drop_table("talent_pool_grants")
