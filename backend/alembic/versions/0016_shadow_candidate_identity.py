"""Shadow foundation: candidate_users, candidate_refresh_tokens, phantom_passports,
passport_personal_info, passport_career_entries.

Deliberately no Row Level Security on any of these tables — RLS in this app enforces
company-tenant isolation via company_id, and none of these tables have a company_id column. A
candidate is not scoped to any company: their Phantom Passport is built once and (once the
Shadow job board exists) applied to many companies' projects. Authorization here is enforced at
the application layer instead — every phantom_passport/candidate_auth query is explicitly
filtered by the candidate's own id taken from their JWT, never from the URL — and every route
runs on the app_auth connection (BYPASSRLS), same as pre-tenant company auth flows (signup/
login/refresh), since app_auth's whole reason for existing is "flows that must run before/
without a tenant context." See app/modules/candidate_auth/__init__.py.

No explicit GRANTs needed here — migration 0001's `ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ... TO app_runtime, app_auth` already covers every table created after it, including these.

Revision ID: 0016
Revises: 0015
Create Date: 2026-08-11

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- candidate_users -------------------------------------------------------------------
    op.create_table(
        "candidate_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_candidate_users_email", "candidate_users", ["email"], unique=True)

    # --- candidate_refresh_tokens ------------------------------------------------------------
    op.create_table(
        "candidate_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_candidate_refresh_tokens_candidate_user_id",
        "candidate_refresh_tokens",
        ["candidate_user_id"],
    )
    op.create_index(
        "ix_candidate_refresh_tokens_token_hash",
        "candidate_refresh_tokens",
        ["token_hash"],
        unique=True,
    )

    # --- phantom_passports ---------------------------------------------------------------------
    op.create_table(
        "phantom_passports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("headline", sa.String(255), nullable=True),
        sa.Column("seniority", sa.String(100), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("industries", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("remote_preference", sa.String(20), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("notice_period", sa.String(20), nullable=True),
        sa.Column("career_intent", sa.String(30), nullable=False, server_default="just_exploring"),
        sa.Column(
            "verification_status", sa.String(20), nullable=False, server_default="unverified"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_phantom_passports_candidate_user_id",
        "phantom_passports",
        ["candidate_user_id"],
        unique=True,
    )

    # --- passport_personal_info ---------------------------------------------------------------
    op.create_table(
        "passport_personal_info",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "passport_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phantom_passports.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("legal_name_encrypted", sa.Text(), nullable=False),
        sa.Column("phone_encrypted", sa.Text(), nullable=True),
        sa.Column("address_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_passport_personal_info_passport_id",
        "passport_personal_info",
        ["passport_id"],
        unique=True,
    )

    # --- passport_career_entries ---------------------------------------------------------------
    op.create_table(
        "passport_career_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "passport_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phantom_passports.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company_name_encrypted", sa.Text(), nullable=False),
        sa.Column("company_name_anonymized", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("achievements", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_passport_career_entries_passport_id", "passport_career_entries", ["passport_id"]
    )

    # Explicit, not relying on migration 0001's `ALTER DEFAULT PRIVILEGES` alone — that covers
    # future tables created by the same role in principle, but this environment's history
    # (candidate_ref_seq's grant needed the same explicit treatment in migration 0013) shows
    # that default privileges alone aren't a safe thing to depend on here. app_auth in
    # particular needs this: every candidate_auth/phantom_passport route runs on the app_auth
    # (BYPASSRLS) connection, not app_runtime — see app/modules/candidate_auth/__init__.py.
    for table in (
        "candidate_users",
        "candidate_refresh_tokens",
        "phantom_passports",
        "passport_personal_info",
        "passport_career_entries",
    ):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_runtime, app_auth")


def downgrade() -> None:
    op.drop_table("passport_career_entries")
    op.drop_table("passport_personal_info")
    op.drop_table("phantom_passports")
    op.drop_table("candidate_refresh_tokens")
    op.drop_table("candidate_users")
