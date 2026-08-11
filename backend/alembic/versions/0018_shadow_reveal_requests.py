"""Shadow Reveal Request workflow: shadow_reveal_requests table. One request per
shadow_application (unique constraint) — a company asks once, the candidate decides once; a
declined or unanswered request is not retried automatically (deferred: an explicit re-request
flow, see app/modules/shadow_reveal/__init__.py).

Same dual-grant treatment as shadow_jobs/shadow_applications in migration 0017: RLS by
company_id for the company side (app_runtime), explicit GRANT to app_auth too since the
candidate approves/declines their own request through the app_auth connection, bypassing RLS,
filtered explicitly by candidate_user_id in application code.

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-11

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shadow_reveal_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column(
            "shadow_application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_applications.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_shadow_reveal_requests_company_id", "shadow_reveal_requests", ["company_id"]
    )
    op.create_index(
        "ix_shadow_reveal_requests_shadow_application_id",
        "shadow_reveal_requests",
        ["shadow_application_id"],
        unique=True,
    )

    op.execute("ALTER TABLE shadow_reveal_requests ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shadow_reveal_requests FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_shadow_reveal_requests ON shadow_reveal_requests
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON shadow_reveal_requests TO app_runtime, app_auth"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_shadow_reveal_requests ON shadow_reveal_requests"
    )
    op.execute("ALTER TABLE shadow_reveal_requests NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shadow_reveal_requests DISABLE ROW LEVEL SECURITY")
    op.drop_table("shadow_reveal_requests")
