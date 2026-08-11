"""Security: project_members table for resource-level (ABAC) authorization

Prior to this, any user with the candidates.view/projects.view permission could see every
project and candidate in their company, scoped only by role, not by which project they were
actually assigned to. This adds a project_members junction table; Owner/Admin still get
company-wide access (unchanged), but a Member-role user must now be an explicit project member.

Backfills every existing project's creator and hiring_manager (if set) as members, so no
currently-working Member-role user loses access to a project they were already using.

Revision ID: 0019
Revises: 0018
Create Date: 2026-08-11

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_members",
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
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_members"),
    )
    op.create_index("ix_project_members_company_id", "project_members", ["company_id"])
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])

    op.execute("ALTER TABLE project_members ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_members FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_project_members ON project_members
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON project_members TO app_runtime")

    # Backfill: creator always becomes a member; hiring_manager too, if one is set. Uses
    # gen_random_uuid() (already relied on elsewhere in this schema via pgcrypto) for the id.
    op.execute(
        """
        INSERT INTO project_members (id, company_id, project_id, user_id, created_at)
        SELECT gen_random_uuid(), company_id, id, created_by_id, now()
        FROM projects
        ON CONFLICT ON CONSTRAINT uq_project_members DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO project_members (id, company_id, project_id, user_id, created_at)
        SELECT gen_random_uuid(), company_id, id, hiring_manager_id, now()
        FROM projects
        WHERE hiring_manager_id IS NOT NULL
        ON CONFLICT ON CONSTRAINT uq_project_members DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_project_members ON project_members")
    op.execute("ALTER TABLE project_members NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_members DISABLE ROW LEVEL SECURITY")
    op.drop_table("project_members")
