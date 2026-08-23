"""Applicant Notes: a private, recruiter-team-only note thread on a Shadow applicant. Never
candidate-visible, never part of any candidate-facing schema or route -- company-only data, so
(unlike messages/interviews) there is no candidate-path GRANT at all, mirroring
project_members'/interview_participants' exact company-only shape.

No new permission -- reuses the existing shadow_jobs.view permission for both read and write
(any team member who can see this applicant at all can add a note; this is an internal
collaboration feature, not a sensitive/elevated action).

Revision ID: 0052
Revises: 0051
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0052"
down_revision: str | None = "0051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "applicant_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "shadow_application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_applications.id"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_applicant_notes_shadow_application_id", "applicant_notes", ["shadow_application_id"]
    )
    op.create_index("ix_applicant_notes_company_id", "applicant_notes", ["company_id"])

    op.execute("ALTER TABLE applicant_notes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE applicant_notes FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_applicant_notes ON applicant_notes
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON applicant_notes TO app_runtime")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_applicant_notes ON applicant_notes")
    op.execute("ALTER TABLE applicant_notes NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE applicant_notes DISABLE ROW LEVEL SECURITY")
    op.drop_table("applicant_notes")
