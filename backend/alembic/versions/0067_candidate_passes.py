"""Anonymous Candidate Discovery Phase 1: candidate_passes -- a recruiter's "not right for this"
(or "not right for us at all") decision on an anonymous candidate found via search.

Company-scoped only, same RLS-by-company_id treatment as talent_pool_grants (0046) -- but GRANT
is app_runtime ONLY, not app_auth, since (unlike talent_pool_grants) a candidate never sees who
passed on them through their own app_auth connection. No new permission: passing reuses the
existing shadow_candidates.search permission (the same people who can search can pass what they
find), per the Phase 1 plan's "don't invent a permission for every new verb" discipline.

Revision ID: 0067
Revises: 0066
Create Date: 2026-08-30

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0067"
down_revision: str | None = "0066"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_passes",
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
            nullable=True,
        ),
        sa.Column("reason", sa.String(50), nullable=True),
        sa.Column(
            "actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_candidate_passes_company_id", "candidate_passes", ["company_id"])
    op.create_index(
        "ix_candidate_passes_candidate_user_id", "candidate_passes", ["candidate_user_id"]
    )

    op.execute("ALTER TABLE candidate_passes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE candidate_passes FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_candidate_passes ON candidate_passes
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON candidate_passes TO app_runtime")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_candidate_passes ON candidate_passes")
    op.execute("ALTER TABLE candidate_passes NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE candidate_passes DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_candidate_passes_candidate_user_id", table_name="candidate_passes")
    op.drop_index("ix_candidate_passes_company_id", table_name="candidate_passes")
    op.drop_table("candidate_passes")
