"""Phase 5: intelligence_packs table, tenant-isolation RLS

No new permissions — reuses candidates.update (trigger generation) / candidates.view (read
result), same reasoning as Phase 4's sanitized_profiles.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intelligence_packs",
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
        sa.Column("skills", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("experience_summary", sa.Text(), nullable=False),
        sa.Column("education", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("narrative_summary", sa.Text(), nullable=False),
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
    op.create_index("ix_intelligence_packs_company_id", "intelligence_packs", ["company_id"])
    op.create_index(
        "ix_intelligence_packs_candidate_id", "intelligence_packs", ["candidate_id"], unique=True
    )

    op.execute("ALTER TABLE intelligence_packs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE intelligence_packs FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_intelligence_packs ON intelligence_packs
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON intelligence_packs TO app_runtime")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_intelligence_packs ON intelligence_packs")
    op.execute("ALTER TABLE intelligence_packs NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE intelligence_packs DISABLE ROW LEVEL SECURITY")
    op.drop_table("intelligence_packs")
