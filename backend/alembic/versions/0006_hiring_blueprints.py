"""Phase 6: projects.role_brief column, hiring_blueprints table, tenant-isolation RLS

No new permissions — reuses projects.update (generate) / projects.view (read result), same
reasoning as Phase 4's sanitized_profiles and Phase 5's intelligence_packs.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("role_brief", sa.Text(), nullable=True))

    op.create_table(
        "hiring_blueprints",
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
            unique=True,
        ),
        sa.Column("role_summary", sa.Text(), nullable=False),
        sa.Column("key_responsibilities", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column(
            "must_have_qualifications", postgresql.JSONB, nullable=False, server_default="[]"
        ),
        sa.Column(
            "nice_to_have_qualifications", postgresql.JSONB, nullable=False, server_default="[]"
        ),
        sa.Column("evaluation_criteria", postgresql.JSONB, nullable=False, server_default="[]"),
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
    op.create_index("ix_hiring_blueprints_company_id", "hiring_blueprints", ["company_id"])
    op.create_index(
        "ix_hiring_blueprints_project_id", "hiring_blueprints", ["project_id"], unique=True
    )

    op.execute("ALTER TABLE hiring_blueprints ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hiring_blueprints FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_hiring_blueprints ON hiring_blueprints
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON hiring_blueprints TO app_runtime")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_hiring_blueprints ON hiring_blueprints")
    op.execute("ALTER TABLE hiring_blueprints NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hiring_blueprints DISABLE ROW LEVEL SECURITY")
    op.drop_table("hiring_blueprints")

    op.drop_column("projects", "role_brief")
