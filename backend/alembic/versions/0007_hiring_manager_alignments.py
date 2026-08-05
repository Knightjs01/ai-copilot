"""Phase 7: hiring_manager_alignments table, tenant-isolation RLS

No new permissions — reuses projects.update (submit) / projects.view (read result), same
reasoning as Phase 5's intelligence_packs and Phase 6's hiring_blueprints.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hiring_manager_alignments",
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
        sa.Column("top_requirements", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column(
            "submitted_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_hiring_manager_alignments_company_id", "hiring_manager_alignments", ["company_id"]
    )
    op.create_index(
        "ix_hiring_manager_alignments_project_id",
        "hiring_manager_alignments",
        ["project_id"],
        unique=True,
    )

    op.execute("ALTER TABLE hiring_manager_alignments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hiring_manager_alignments FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_hiring_manager_alignments ON hiring_manager_alignments
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON hiring_manager_alignments TO app_runtime")


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_hiring_manager_alignments "
        "ON hiring_manager_alignments"
    )
    op.execute("ALTER TABLE hiring_manager_alignments NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hiring_manager_alignments DISABLE ROW LEVEL SECURITY")
    op.drop_table("hiring_manager_alignments")
