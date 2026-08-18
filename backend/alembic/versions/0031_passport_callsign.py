"""Persistent Passport Callsign: a stable, candidate-only identity generated once at first
Passport approval — distinct from shadow_jobs' per-application Callsigns (regenerated fresh for
every job application, deliberately, so applying to two roles never links back to the same
person). This one lives on the Passport itself and is only ever returned to its owning candidate
via GET /phantom-passport/me — never surfaced on any company-facing schema.

No RLS/GRANT changes needed — phantom_passports is a candidate-owned table (no company_id
scoping), already covered by migration 0001's ALTER DEFAULT PRIVILEGES for app_runtime/app_auth.

Revision ID: 0031
Revises: 0030
Create Date: 2026-08-19

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("phantom_passports", sa.Column("callsign", sa.String(50), nullable=True))
    op.create_index("ix_phantom_passports_callsign", "phantom_passports", ["callsign"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_phantom_passports_callsign", table_name="phantom_passports")
    op.drop_column("phantom_passports", "callsign")
