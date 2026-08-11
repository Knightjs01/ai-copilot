"""Shadow job board: shadow_jobs (company-posted listings), shadow_applications
(candidate applications, one per candidate per job), shadow_jobs.* permissions.

Both tables carry company_id and get standard tenant-isolation RLS for the company side
(job posting, applicant review — always via app_runtime/get_tenant_db). But candidates are
not scoped to any company (see migration 0016), and the public job board must show published
jobs across every company, not just one tenant — so both tables also get an explicit GRANT to
app_auth. app_auth is BYPASSRLS, so the RLS policy below has no effect on it; every
candidate-facing query in the shadow_jobs module filters explicitly in application code instead
(by candidate_user_id from the JWT, exactly like phantom_passport) rather than relying on RLS.

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-11

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels = None
depends_on = None

_NEW_PERMISSIONS = [
    (uuid.uuid4(), "shadow_jobs.create", "Post jobs to the Shadow job board"),
    (uuid.uuid4(), "shadow_jobs.view", "View Shadow job postings and their anonymized applicants"),
    (uuid.uuid4(), "shadow_jobs.update", "Edit, publish, or close Shadow job postings"),
]
_OWNER_AND_ADMIN_CODES = ["shadow_jobs.create", "shadow_jobs.view", "shadow_jobs.update"]
_MEMBER_CODES = ["shadow_jobs.view"]


def upgrade() -> None:
    # --- shadow_jobs -------------------------------------------------------------------------
    op.create_table(
        "shadow_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=True,
            unique=True,
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("seniority", sa.String(100), nullable=True),
        sa.Column("employment_type", sa.String(20), nullable=False, server_default="full_time"),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("remote_preference", sa.String(20), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_shadow_jobs_company_id", "shadow_jobs", ["company_id"])
    op.create_index("ix_shadow_jobs_status_published_at", "shadow_jobs", ["status", "published_at"])

    op.execute("ALTER TABLE shadow_jobs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shadow_jobs FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_shadow_jobs ON shadow_jobs
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON shadow_jobs TO app_runtime, app_auth")

    # --- shadow_applications -------------------------------------------------------------------
    op.create_table(
        "shadow_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column(
            "shadow_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column(
            "phantom_passport_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phantom_passports.id"),
            nullable=False,
        ),
        sa.Column("callsign", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="submitted"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "shadow_job_id", "candidate_user_id", name="uq_shadow_application_job_candidate"
        ),
        sa.UniqueConstraint("shadow_job_id", "callsign", name="uq_shadow_application_job_callsign"),
    )
    op.create_index("ix_shadow_applications_company_id", "shadow_applications", ["company_id"])
    op.create_index(
        "ix_shadow_applications_shadow_job_id", "shadow_applications", ["shadow_job_id"]
    )
    op.create_index(
        "ix_shadow_applications_candidate_user_id", "shadow_applications", ["candidate_user_id"]
    )

    op.execute("ALTER TABLE shadow_applications ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shadow_applications FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_shadow_applications ON shadow_applications
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON shadow_applications TO app_runtime, app_auth"
    )

    # --- permissions -----------------------------------------------------------------------
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
    member_codes = ", ".join(f"'{code}'" for code in _MEMBER_CODES)
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ({owner_admin_codes}))
        """
    )
    op.execute(
        f"""
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code IN ({member_codes}))
        """
    )
    op.execute(f"DELETE FROM permissions WHERE code IN ({owner_admin_codes})")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_shadow_applications ON shadow_applications")
    op.execute("ALTER TABLE shadow_applications NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shadow_applications DISABLE ROW LEVEL SECURITY")
    op.drop_table("shadow_applications")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_shadow_jobs ON shadow_jobs")
    op.execute("ALTER TABLE shadow_jobs NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shadow_jobs DISABLE ROW LEVEL SECURITY")
    op.drop_table("shadow_jobs")
