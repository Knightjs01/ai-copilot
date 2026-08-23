"""shadow_applications: persist decrypted career history once revealed.

Mirrors migration 0055's revealed_full_name/revealed_email/revealed_phone pattern -- once a
company completes the "Reveal Identity" action for an application and career history is part of
the approved disclosure, the decrypted employer names (plus dates/responsibilities/achievements,
which were never encrypted to begin with) get written here too, so the anonymized-CV dialog and
any other surface reading this application's history don't need a fresh per-session reveal to see
it again. Populated exactly once, by ShadowRevealService.get_revealed_identity, nullable (NULL
means "never revealed" or "career history wasn't part of the disclosure"), no backfill.

Revision ID: 0057
Revises: 0056
Create Date: 2026-08-23

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0057"
down_revision: str | None = "0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shadow_applications",
        sa.Column(
            "revealed_career_entries",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("shadow_applications", "revealed_career_entries")
