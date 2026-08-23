"""Interview Scorecards: one row per (interview, submitting interviewer) -- each interviewer
submits their own independent structured scorecard, competencies AI-derived from their own typed
notes (never a fixed taxonomy), interviewer confirms before saving. Company-only data, mirrors
applicant_notes'/interview_participants' exact company-only shape -- no candidate-facing route,
no app_auth grant.

Revision ID: 0056
Revises: 0055
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0056"
down_revision: str | None = "0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_scorecards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "interview_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "submitted_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column(
            "competency_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("overall_recommendation", sa.String(length=20), nullable=False),
        sa.Column("model_used", sa.String(length=100), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_interview_scorecards_interview_id", "interview_scorecards", ["interview_id"]
    )
    op.create_index("ix_interview_scorecards_company_id", "interview_scorecards", ["company_id"])
    op.create_unique_constraint(
        "uq_interview_scorecards_interview_user",
        "interview_scorecards",
        ["interview_id", "submitted_by_user_id"],
    )

    op.execute("ALTER TABLE interview_scorecards ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interview_scorecards FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_interview_scorecards ON interview_scorecards
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON interview_scorecards TO app_runtime")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_interview_scorecards ON interview_scorecards")
    op.execute("ALTER TABLE interview_scorecards NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interview_scorecards DISABLE ROW LEVEL SECURITY")
    op.drop_table("interview_scorecards")
