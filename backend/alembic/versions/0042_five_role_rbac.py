"""Five-role RBAC: Owner/Admin/Member becomes Owner/TA Admin/Recruiter/Hiring Manager/Interviewer.

Roles are per-company rows (roles.name is only unique per company_id), so every existing company
needs this migrated in place, not just new signups going forward through the updated
ROLE_PERMISSIONS dict in auth/permissions.py.

- Admin -> TA Admin and Member -> Recruiter are renamed in place (UPDATE ... SET name), preserving
  every existing role_permissions/user_roles FK -- no user loses their role, no re-assignment
  needed.
- Hiring Manager and Interviewer are genuinely new roles, inserted per existing company (mirrors
  0019_project_members.py's exact backfill idiom: INSERT ... SELECT ... FROM companies with
  gen_random_uuid()).
- New permission code hiring_manager_alignment.submit replaces the old PROJECTS_UPDATE gate on
  submitting hiring-manager top-requirements, so Hiring Manager can be granted just that action
  without the broader project-edit rights PROJECTS_UPDATE also carries.
- Recruiter (renamed from Member) is a deliberate permission *expansion*, not a pure rename --
  confirmed with the user: create/update candidates, post/manage Shadow jobs, send messages,
  schedule interviews. Old Member never had any of these.

Also creates interview_participants (mirrors project_members exactly) -- the resource-scoping
table the new Interviewer role needs, since nothing interview-instance-scoped existed before this.

Revision ID: 0042
Revises: 0041
Create Date: 2026-08-20

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0042"
down_revision: str | None = "0041"
branch_labels = None
depends_on = None

_NEW_PERMISSIONS = [
    (
        uuid.uuid4(),
        "hiring_manager_alignment.submit",
        "Submit hiring-manager top-requirements for a project",
    ),
]

_HIRING_MANAGER_CODES = [
    "users.view",
    "projects.view",
    "candidates.view",
    "hiring_manager_alignment.submit",
]
_INTERVIEWER_CODES = ["users.view", "interviews.view"]
_OWNER_TA_ADMIN_NEW_CODES = ["hiring_manager_alignment.submit"]
_RECRUITER_NEW_CODES = [
    "candidates.create",
    "candidates.update",
    "shadow_jobs.create",
    "shadow_jobs.update",
    "messages.send",
    "interviews.schedule",
]


def upgrade() -> None:
    # --- Rename Admin -> TA Admin, Member -> Recruiter, in place --------------------------------
    op.execute("UPDATE roles SET name = 'TA Admin' WHERE name = 'Admin'")
    op.execute("UPDATE roles SET name = 'Recruiter' WHERE name = 'Member'")

    # --- New system roles per existing company ---------------------------------------------------
    op.execute(
        """
        INSERT INTO roles (id, company_id, name, is_system, created_at, updated_at)
        SELECT gen_random_uuid(), id, 'Hiring Manager', true, now(), now()
        FROM companies
        ON CONFLICT ON CONSTRAINT uq_roles_company_name DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO roles (id, company_id, name, is_system, created_at, updated_at)
        SELECT gen_random_uuid(), id, 'Interviewer', true, now(), now()
        FROM companies
        ON CONFLICT ON CONSTRAINT uq_roles_company_name DO NOTHING
        """
    )

    # --- New permission catalog entry -------------------------------------------------------------
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

    # --- Grant matrix --------------------------------------------------------------------------
    hiring_manager_codes = ", ".join(f"'{code}'" for code in _HIRING_MANAGER_CODES)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'Hiring Manager' AND p.code IN ({hiring_manager_codes})
        ON CONFLICT DO NOTHING
        """
    )

    interviewer_codes = ", ".join(f"'{code}'" for code in _INTERVIEWER_CODES)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'Interviewer' AND p.code IN ({interviewer_codes})
        ON CONFLICT DO NOTHING
        """
    )

    owner_ta_admin_codes = ", ".join(f"'{code}'" for code in _OWNER_TA_ADMIN_NEW_CODES)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name IN ('Owner', 'TA Admin') AND p.code IN ({owner_ta_admin_codes})
        ON CONFLICT DO NOTHING
        """
    )

    recruiter_codes = ", ".join(f"'{code}'" for code in _RECRUITER_NEW_CODES)
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'Recruiter' AND p.code IN ({recruiter_codes})
        ON CONFLICT DO NOTHING
        """
    )

    # --- interview_participants: resource-scoping table for the Interviewer role -----------------
    op.create_table(
        "interview_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "interview_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("interview_id", "user_id", name="uq_interview_participants"),
    )
    op.create_index(
        "ix_interview_participants_company_id", "interview_participants", ["company_id"]
    )
    op.create_index(
        "ix_interview_participants_interview_id", "interview_participants", ["interview_id"]
    )
    op.create_index("ix_interview_participants_user_id", "interview_participants", ["user_id"])

    op.execute("ALTER TABLE interview_participants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interview_participants FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_interview_participants ON interview_participants
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    # app_runtime (company path) gets full CRUD -- only company-side code ever assigns
    # interviewers. app_auth (candidate path) gets SELECT only -- InterviewService._to_read /
    # list_for_candidate read interview_participants when building a candidate's own interview
    # view (get_for_candidate, list_for_candidate both run on get_db/app_auth), but a candidate
    # never writes to this table.
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON interview_participants TO app_runtime")
    op.execute("GRANT SELECT ON interview_participants TO app_auth")

    # Backfill: whoever scheduled an existing interview becomes its first participant, so nobody
    # currently able to see an interview they booked loses that access if later moved to
    # Interviewer-only.
    op.execute(
        """
        INSERT INTO interview_participants (id, company_id, interview_id, user_id, created_at)
        SELECT gen_random_uuid(), company_id, id, scheduled_by_user_id, now()
        FROM interviews
        WHERE scheduled_by_user_id IS NOT NULL
        ON CONFLICT ON CONSTRAINT uq_interview_participants DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_interview_participants ON interview_participants"
    )
    op.execute("ALTER TABLE interview_participants NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE interview_participants DISABLE ROW LEVEL SECURITY")
    op.drop_table("interview_participants")

    recruiter_codes = ", ".join(f"'{code}'" for code in _RECRUITER_NEW_CODES)
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE role_id IN (SELECT id FROM roles WHERE name = 'Recruiter')
        AND permission_id IN (SELECT id FROM permissions WHERE code IN ({recruiter_codes}))
        """
    )

    new_permission_codes = ", ".join(f"'{code}'" for _, code, _ in _NEW_PERMISSIONS)
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ({new_permission_codes}))
        """
    )
    op.execute(f"DELETE FROM permissions WHERE code IN ({new_permission_codes})")

    op.execute(
        """
        DELETE FROM user_roles
        WHERE role_id IN (SELECT id FROM roles WHERE name IN ('Hiring Manager', 'Interviewer'))
        """
    )
    op.execute(
        """
        DELETE FROM role_permissions
        WHERE role_id IN (SELECT id FROM roles WHERE name IN ('Hiring Manager', 'Interviewer'))
        """
    )
    op.execute("DELETE FROM roles WHERE name IN ('Hiring Manager', 'Interviewer')")

    op.execute("UPDATE roles SET name = 'Admin' WHERE name = 'TA Admin'")
    op.execute("UPDATE roles SET name = 'Member' WHERE name = 'Recruiter'")
