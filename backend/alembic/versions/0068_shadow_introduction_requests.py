"""Anonymous Candidate Discovery Phase 2: shadow_introduction_requests -- the third, distinct
candidate<->company consent mechanism (alongside shadow_reveal_requests and talent_pool_grants).
A recruiter finds an anonymous candidate via search and asks whether they're open to a
conversation about a specific role; the candidate accepts or declines without their identity
ever being disclosed by this action. Always job-scoped, matching how candidate search itself is
job-scoped -- there is no generic, job-less candidate browse in this product today.

A hard unique constraint on (candidate_user_id, company_id, shadow_job_id) would permanently
block re-requesting after a decline, so this uses a partial unique index instead (mirrors
migration 0046's talent_pool_grants precedent exactly), covering only the "pending" status -- a
fresh request is always possible once a prior one has been declined (accepted rows also block a
duplicate, since re-requesting someone already in the pipeline for this role makes no sense).

Same dual-grant treatment as talent_pool_grants (0046): RLS by company_id for the company side
(app_runtime), explicit GRANT to app_auth too since the candidate views/responds to their own
requests through the app_auth connection, bypassing RLS, filtered explicitly by
candidate_user_id in application code.

New permission shadow_introduction.request -- Owner (auto) + TA Admin + Recruiter get it, same
role set as talent_pool.request/shadow_candidates.search (day-to-day Shadow candidate-search
work); Hiring Manager and Interviewer get neither.

Revision ID: 0068
Revises: 0067
Create Date: 2026-08-30

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0068"
down_revision: str | None = "0067"
branch_labels = None
depends_on = None

_PERMISSION_CODE = "shadow_introduction.request"
_PERMISSION_DESCRIPTION = "Ask a discoverable Shadow candidate to start a conversation"


def upgrade() -> None:
    op.create_table(
        "shadow_introduction_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column(
            "shadow_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resulting_application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_applications.id", ondelete="SET NULL"),
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
        "ix_shadow_introduction_requests_company_id",
        "shadow_introduction_requests",
        ["company_id"],
    )
    op.create_index(
        "ix_shadow_introduction_requests_candidate_user_id",
        "shadow_introduction_requests",
        ["candidate_user_id"],
    )
    op.create_index(
        "ix_shadow_introduction_requests_shadow_job_id",
        "shadow_introduction_requests",
        ["shadow_job_id"],
    )
    op.create_index(
        "uq_shadow_introduction_requests_active_triple",
        "shadow_introduction_requests",
        ["candidate_user_id", "company_id", "shadow_job_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'accepted')"),
    )

    op.execute("ALTER TABLE shadow_introduction_requests ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shadow_introduction_requests FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_shadow_introduction_requests ON shadow_introduction_requests
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON shadow_introduction_requests TO app_runtime, app_auth"
    )

    permission_id = uuid.uuid4()
    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        permissions_table,
        [{"id": permission_id, "code": _PERMISSION_CODE, "description": _PERMISSION_DESCRIPTION}],
    )
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name IN ('Owner', 'TA Admin', 'Recruiter') AND p.code = '{_PERMISSION_CODE}'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code = '{_PERMISSION_CODE}')
        """
    )
    op.execute(f"DELETE FROM permissions WHERE code = '{_PERMISSION_CODE}'")

    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_shadow_introduction_requests "
        "ON shadow_introduction_requests"
    )
    op.execute("ALTER TABLE shadow_introduction_requests NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shadow_introduction_requests DISABLE ROW LEVEL SECURITY")
    op.drop_index(
        "uq_shadow_introduction_requests_active_triple",
        table_name="shadow_introduction_requests",
    )
    op.drop_index(
        "ix_shadow_introduction_requests_shadow_job_id", table_name="shadow_introduction_requests"
    )
    op.drop_index(
        "ix_shadow_introduction_requests_candidate_user_id",
        table_name="shadow_introduction_requests",
    )
    op.drop_index(
        "ix_shadow_introduction_requests_company_id", table_name="shadow_introduction_requests"
    )
    op.drop_table("shadow_introduction_requests")
