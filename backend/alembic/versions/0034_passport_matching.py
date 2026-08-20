"""Passport Matching: passport_job_matches, the first two-FK AI-result cache table in this
codebase — keyed on (passport_version_id, shadow_job_id). Structurally dual-audience like
shadow_jobs/shadow_applications (a company's job + a candidate's own passport), not candidate-only
like saved_shadow_jobs, so it gets both RLS (company/future-recruiter path) and an explicit GRANT
to app_auth (candidate path, bypasses RLS, filtered explicitly by passport ownership in the
repository — never trust RLS for the candidate side, same rationale migration 0017 documents).

Revision ID: 0034
Revises: 0033
Create Date: 2026-08-18

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "passport_job_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "passport_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("passport_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "shadow_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_jobs.id"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("match_tier", sa.String(30), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("strengths", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("gaps", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("shadow_job_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "passport_version_id", "shadow_job_id", name="uq_passport_job_match_version_job"
        ),
    )
    op.create_index(
        "ix_passport_job_matches_passport_version_id",
        "passport_job_matches",
        ["passport_version_id"],
    )
    op.create_index(
        "ix_passport_job_matches_shadow_job_id", "passport_job_matches", ["shadow_job_id"]
    )

    op.execute("ALTER TABLE passport_job_matches ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE passport_job_matches FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_passport_job_matches ON passport_job_matches
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON passport_job_matches TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_passport_job_matches ON passport_job_matches")
    op.execute("ALTER TABLE passport_job_matches NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE passport_job_matches DISABLE ROW LEVEL SECURITY")
    op.drop_table("passport_job_matches")
