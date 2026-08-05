"""Phase 8 (Part B): prescreen_assessments table, tenant-isolation RLS

No new permissions — reuses candidates.update (generate) / candidates.view (read result), same
reasoning as Phase 5's intelligence_packs.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prescreen_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("fit_rating", sa.String(20), nullable=False),
        sa.Column("fit_summary", sa.Text(), nullable=False),
        sa.Column("strengths", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("gaps", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("suggested_questions", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("areas_to_probe", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("handoff_recommendations", postgresql.JSONB, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_prescreen_assessments_company_id", "prescreen_assessments", ["company_id"])
    op.create_index(
        "ix_prescreen_assessments_candidate_id",
        "prescreen_assessments",
        ["candidate_id"],
        unique=True,
    )

    op.execute("ALTER TABLE prescreen_assessments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE prescreen_assessments FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_prescreen_assessments ON prescreen_assessments
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON prescreen_assessments TO app_runtime")


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_prescreen_assessments ON prescreen_assessments"
    )
    op.execute("ALTER TABLE prescreen_assessments NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE prescreen_assessments DISABLE ROW LEVEL SECURITY")
    op.drop_table("prescreen_assessments")
