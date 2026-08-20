"""Interviews: real interview scheduling scoped to a Shadow application (date/time, location,
meeting link, status). Structurally dual-audience like messages/shadow_jobs/shadow_reveal:
interviews carries company_id for RLS on the company path, plus an explicit GRANT to app_auth
for the candidate path (which always bypasses RLS via get_db, filtered explicitly by
candidate_user_id in the repository — never trust RLS for that side, same rationale migration
0017/0035 document). No ON DELETE CASCADE needed — interviews has no child rows, and a project
purge deletes rows directly via InterviewRepository.delete_by_shadow_application_ids.

Deliberately does NOT touch candidates.interview_scheduled_at — that's a separate, unlinked ATS
pipeline field (see app/modules/interviews/__init__.py for why).

New permissions interviews.view (Owner+Admin+Member) and interviews.schedule (Owner+Admin) —
mirrors the exact split already established for messages (view is team-wide, mutations are
Owner+Admin only).

Revision ID: 0036
Revises: 0035
Create Date: 2026-08-20

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels = None
depends_on = None

_NEW_PERMISSIONS = [
    (uuid.uuid4(), "interviews.view", "View scheduled interviews for Shadow applicants"),
    (
        uuid.uuid4(),
        "interviews.schedule",
        "Schedule, reschedule, or cancel interviews with a Shadow applicant",
    ),
]
_OWNER_AND_ADMIN_CODES = ["interviews.view", "interviews.schedule"]
_MEMBER_CODES = ["interviews.view"]


def upgrade() -> None:
    op.create_table(
        "interviews",
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
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("meeting_link", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column(
            "scheduled_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_interviews_shadow_application_id", "interviews", ["shadow_application_id"])
    op.create_index("ix_interviews_company_id", "interviews", ["company_id"])
    op.create_index("ix_interviews_candidate_user_id", "interviews", ["candidate_user_id"])

    op.execute("ALTER TABLE interviews ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interviews FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_interviews ON interviews
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON interviews TO app_runtime, app_auth")

    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        permissions_table,
        [{"id": pid, "code": code, "description": desc} for pid, code, desc in _NEW_PERMISSIONS],
    )

    owner_admin_codes = ", ".join(f"'{code}'" for code in _OWNER_AND_ADMIN_CODES)
    member_codes = ", ".join(f"'{code}'" for code in _MEMBER_CODES)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name IN ('Owner', 'Admin') AND p.code IN ({owner_admin_codes})
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'Member' AND p.code IN ({member_codes})
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    owner_admin_codes = ", ".join(f"'{code}'" for code in _OWNER_AND_ADMIN_CODES)
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ({owner_admin_codes}))
        """
    )
    op.execute(f"DELETE FROM permissions WHERE code IN ({owner_admin_codes})")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_interviews ON interviews")
    op.execute("ALTER TABLE interviews NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interviews DISABLE ROW LEVEL SECURITY")
    op.drop_table("interviews")
