"""Candidate Vault (original CV storage) and Passport versioning: candidate_cv_documents,
passport_versions, plus phantom_passports.current_version_id and
shadow_applications.passport_version_id.

Reverses phantom_passport's original zero-file-retention design — the raw CV is now persisted,
private to the candidate, never joined into any recruiter-facing query. Adds an explicit
approval gate (a passport is "approved" iff current_version_id is not null — no separate boolean)
and immutable version snapshots so an already-submitted ShadowApplication keeps showing a
recruiter exactly what was approved at apply time, instead of shadow_jobs's live read silently
rewriting history on every later Passport edit.

Same no-RLS pattern as migration 0016 for candidate_cv_documents/passport_versions — no
company_id exists on any of these rows, authorization is ownership-check-only at the application
layer. shadow_applications already has RLS from migration 0017 (company-scoped); the new column
there is just a plain nullable FK, no RLS change needed.

phantom_passports.current_version_id and passport_versions.passport_id form a two-way FK
relationship between existing and new tables — passport_versions is created first (FKing into
the already-existing phantom_passports.id), then phantom_passports is altered to add
current_version_id (FKing into the now-existing passport_versions.id).

shadow_applications.passport_version_id is nullable and not backfilled: this is a pre-launch app
with no real production data, so any pre-existing dev/test application rows simply have no
version recorded and shadow_jobs falls back to a live read for those — see shadow_jobs/service.py.

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-14

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- candidate_cv_documents ---------------------------------------------------------------
    op.create_table(
        "candidate_cv_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_candidate_cv_documents_candidate_user_id",
        "candidate_cv_documents",
        ["candidate_user_id"],
        unique=True,
    )

    # --- passport_versions ---------------------------------------------------------------------
    op.create_table(
        "passport_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "passport_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phantom_passports.id"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False),
        sa.Column(
            "source_cv_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_cv_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_cv_filename", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_passport_versions_passport_id", "passport_versions", ["passport_id"])
    op.create_unique_constraint(
        "uq_passport_versions_passport_id_version_number",
        "passport_versions",
        ["passport_id", "version_number"],
    )

    # --- phantom_passports.current_version_id ---------------------------------------------------
    op.add_column(
        "phantom_passports",
        sa.Column(
            "current_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("passport_versions.id"),
            nullable=True,
        ),
    )

    # --- shadow_applications.passport_version_id -------------------------------------------------
    op.add_column(
        "shadow_applications",
        sa.Column(
            "passport_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("passport_versions.id"),
            nullable=True,
        ),
    )

    for table in ("candidate_cv_documents", "passport_versions"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_runtime, app_auth")


def downgrade() -> None:
    op.drop_column("shadow_applications", "passport_version_id")
    op.drop_column("phantom_passports", "current_version_id")
    op.drop_table("passport_versions")
    op.drop_table("candidate_cv_documents")
