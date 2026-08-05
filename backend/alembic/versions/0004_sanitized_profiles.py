"""Phase 4: sanitized_profiles table, tenant-isolation RLS

No new permissions in this migration — the Privacy Gateway reuses candidates.update (to trigger
sanitize) and candidates.view (to read the result), since it's operationally part of managing a
candidate's data rather than a distinct resource needing its own access control.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sanitized_profiles",
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
        sa.Column("redacted_text", sa.Text(), nullable=False),
        sa.Column("redaction_counts", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("source_file_type", sa.String(10), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sanitized_profiles_company_id", "sanitized_profiles", ["company_id"])
    op.create_index(
        "ix_sanitized_profiles_candidate_id", "sanitized_profiles", ["candidate_id"], unique=True
    )

    op.execute("ALTER TABLE sanitized_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sanitized_profiles FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_sanitized_profiles ON sanitized_profiles
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON sanitized_profiles TO app_runtime")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_sanitized_profiles ON sanitized_profiles")
    op.execute("ALTER TABLE sanitized_profiles NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sanitized_profiles DISABLE ROW LEVEL SECURITY")
    op.drop_table("sanitized_profiles")
