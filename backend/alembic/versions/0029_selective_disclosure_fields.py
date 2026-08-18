"""Selective-disclosure reveal fields: adds a nullable disclosed_fields JSONB column to both
identity_reveal_events and shadow_reveal_requests.

Extends the existing 3-tier DisclosureLevel (basic/contact/full, migration 0024) with true
per-field selective disclosure. The tier system stays as a convenience default; this column
records the exact resolved set of fields a reveal actually disclosed, whether that came from an
explicit selection or a tier default — see app.core.disclosure.IDENTITY_TIER_FIELDS /
SHADOW_TIER_FIELDS for the backward-compat mapping.

No backfill: old rows stay NULL (both service layers already treat a NULL/missing selection as
"fall back to the tier default," so this is a safe no-op for historic reveals). Both target
tables already have RLS policies and grants from their original migrations (0013-family, 0018) —
adding a column needs no re-grant.

Revision ID: 0029
Revises: 0028
Create Date: 2026-08-18

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0029"
down_revision: str | None = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "identity_reveal_events",
        sa.Column("disclosed_fields", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "shadow_reveal_requests",
        sa.Column("disclosed_fields", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shadow_reveal_requests", "disclosed_fields")
    op.drop_column("identity_reveal_events", "disclosed_fields")
