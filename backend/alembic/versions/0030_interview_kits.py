"""Interview kits: structured, bias-resistant interview questions grounded 1:1 in the hiring
blueprint's must-have qualifications and evaluation criteria.

No new permissions — reuses projects.update (generate) / projects.view (read result), same
reasoning as hiring_blueprint (0006) and every other blueprint-derived artifact.

Revision ID: 0030
Revises: 0029
Create Date: 2026-08-18

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_kits",
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
        sa.Column("questions", postgresql.JSONB, nullable=False, server_default="[]"),
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
    op.create_index("ix_interview_kits_company_id", "interview_kits", ["company_id"])
    op.create_index("ix_interview_kits_project_id", "interview_kits", ["project_id"], unique=True)

    op.execute("ALTER TABLE interview_kits ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interview_kits FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_interview_kits ON interview_kits
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON interview_kits TO app_runtime")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_interview_kits ON interview_kits")
    op.execute("ALTER TABLE interview_kits NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interview_kits DISABLE ROW LEVEL SECURITY")
    op.drop_table("interview_kits")
