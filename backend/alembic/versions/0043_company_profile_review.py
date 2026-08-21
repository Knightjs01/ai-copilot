"""Company Profile Builder rework: replaces the flat is_profile_public boolean with a real,
staff-reviewed publish-state machine (draft/pending_review/live/paused/suspended), plus a new
company_profile_versions table -- an immutable per-approval snapshot, mirroring PassportVersion
exactly (one JSONB blob per version, not one column per field). Company's own description/
culture/benefits/size/industry columns become the live-editable *draft*; GET /companies/{slug}
now reads from current_profile_version_id's snapshot instead, so a company can keep editing
without touching what's currently public.

Also adds logo_storage_key/cover_image_storage_key/hiring_process_overview -- the new
employer-brand-media and hiring-profile fields.

Backfill: every company with is_profile_public = true gets a real version 1 snapshot built from
its current fields (approved_by_admin_id NULL -- a real, honest grandfather case, since no admin
actually reviewed these under the old boolean-only system) and profile_status flips to 'live'.
Every other company defaults to 'draft'. Only then is is_profile_public dropped.

No RLS -- companies/company_profile_versions are not tenant-isolated tables (see 0001's own
companies table, queried via both the RLS-bypass app_auth role for admin/public routes and the
app_runtime role for the authenticated self-service routes) -- grants to both.

Revision ID: 0043
Revises: 0042
Create Date: 2026-08-20

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0043"
down_revision: str | None = "0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_profile_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "approved_by_admin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_admins.id"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "version_number", name="uq_company_profile_versions"),
    )
    op.create_index(
        "ix_company_profile_versions_company_id", "company_profile_versions", ["company_id"]
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON company_profile_versions TO app_runtime, app_auth"
    )

    op.add_column(
        "companies",
        sa.Column("profile_status", sa.String(20), nullable=False, server_default="draft"),
    )
    op.add_column(
        "companies",
        sa.Column(
            "current_profile_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("company_profile_versions.id"),
            nullable=True,
        ),
    )
    op.add_column("companies", sa.Column("logo_storage_key", sa.String(512), nullable=True))
    op.add_column("companies", sa.Column("cover_image_storage_key", sa.String(512), nullable=True))
    op.add_column("companies", sa.Column("hiring_process_overview", sa.Text(), nullable=True))

    op.execute(
        """
        INSERT INTO company_profile_versions
            (id, company_id, version_number, snapshot, approved_by_admin_id, approved_at)
        SELECT
            gen_random_uuid(),
            id,
            1,
            jsonb_build_object(
                'name', name,
                'slug', slug,
                'description', description,
                'culture', culture,
                'benefits', benefits,
                'size', size,
                'industry', industry,
                'logo_url', NULL,
                'cover_image_url', NULL,
                'hiring_process_overview', NULL
            ),
            NULL,
            now()
        FROM companies
        WHERE is_profile_public = true
        """
    )
    op.execute(
        """
        UPDATE companies c
        SET current_profile_version_id = v.id, profile_status = 'live'
        FROM company_profile_versions v
        WHERE v.company_id = c.id AND c.is_profile_public = true
        """
    )

    op.drop_column("companies", "is_profile_public")


def downgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("is_profile_public", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.execute("UPDATE companies SET is_profile_public = true WHERE profile_status = 'live'")

    op.drop_column("companies", "hiring_process_overview")
    op.drop_column("companies", "cover_image_storage_key")
    op.drop_column("companies", "logo_storage_key")
    op.drop_column("companies", "current_profile_version_id")
    op.drop_column("companies", "profile_status")

    op.drop_index("ix_company_profile_versions_company_id", table_name="company_profile_versions")
    op.drop_table("company_profile_versions")
