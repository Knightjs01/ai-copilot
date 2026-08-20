"""Passport visibility: adds phantom_passports.visibility (private/match_only/discoverable,
default private -- nothing changes for any existing candidate until they explicitly opt in). No
RLS change -- phantom_passports has never had RLS (see 0016_shadow_candidate_identity.py's own
docstring: a Passport is reused across every company, not owned by one, so authorization here is
enforced at the application layer instead). The visibility/career_intent/current_version_id
filter in PhantomPassportRepository.list_discoverable_candidates IS the access-control boundary
for company-side candidate search, same pattern this table already used before this migration.

New permission shadow_candidates.search (Owner+Admin+Member) -- view-tier alongside
shadow_jobs.view, not Owner-exclusive like identity_vault.reveal, since results are anonymized
(no PII, same as every other Shadow-facing card).

Revision ID: 0037
Revises: 0036
Create Date: 2026-08-22

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels = None
depends_on = None

_NEW_PERMISSIONS = [
    (
        uuid.uuid4(),
        "shadow_candidates.search",
        "Search discoverable Shadow candidates ranked by AI match",
    ),
]
_OWNER_AND_ADMIN_CODES = ["shadow_candidates.search"]
_MEMBER_CODES = ["shadow_candidates.search"]


def upgrade() -> None:
    op.add_column(
        "phantom_passports",
        sa.Column("visibility", sa.String(20), nullable=False, server_default="private"),
    )

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

    op.drop_column("phantom_passports", "visibility")
