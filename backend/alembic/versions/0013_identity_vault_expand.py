"""Candidate Identity Vault (expand): candidate_identity_vaults, identity_reveal_events,
callsign/candidate_ref on candidates, backfill from existing candidate PII, identity_vault.reveal
permission (Owner only).

Expand/contract pair with 0014 — this revision only ADDS structure and backfills data; the old
PII columns on candidates stay in place (nullable, now write-only/inert) until 0014 drops them.
Splitting it this way gives an independent rollback point between "vault populated" and "old
columns gone forever," which matters here because dropping full_name/email/phone/etc. is not
reversible with data intact.

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-06

"""

import secrets
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.modules.auth.security import encrypt_secret

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels = None
depends_on = None

_CALLSIGN_WORDS = [
    "Ghost", "Echo", "Shadow", "Phantom", "Nova", "Cipher", "Vector", "Pulse",
    "Atlas", "Orion", "Titan", "Falcon", "Spectre", "Sentinel", "Vanguard",
]  # fmt: skip


def _generate_callsign(used: set[tuple[uuid.UUID, str]], project_id: uuid.UUID) -> str:
    for _ in range(50):
        candidate = f"{secrets.choice(_CALLSIGN_WORDS)}-{secrets.randbelow(90) + 10}"
        if (project_id, candidate) not in used:
            used.add((project_id, candidate))
            return candidate
    raise RuntimeError("Could not generate a unique callsign during backfill")


def upgrade() -> None:
    op.execute("CREATE SEQUENCE candidate_ref_seq")
    # Sequences need their own explicit grant — GRANT ... ON ALL TABLES does not cover them, and
    # app_runtime is the only role that ever calls nextval() on this (via IdentityVaultService).
    op.execute("GRANT USAGE, SELECT ON SEQUENCE candidate_ref_seq TO app_runtime")

    # --- candidate_identity_vaults -----------------------------------------------------------
    op.create_table(
        "candidate_identity_vaults",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("full_name_encrypted", sa.Text(), nullable=False),
        sa.Column("email_encrypted", sa.Text(), nullable=True),
        sa.Column("phone_encrypted", sa.Text(), nullable=True),
        sa.Column("location_encrypted", sa.Text(), nullable=True),
        sa.Column("current_employer_encrypted", sa.Text(), nullable=True),
        sa.Column("current_title_encrypted", sa.Text(), nullable=True),
        sa.Column("linkedin_url_encrypted", sa.Text(), nullable=True),
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
        "ix_candidate_identity_vaults_company_id", "candidate_identity_vaults", ["company_id"]
    )
    op.create_index(
        "ix_candidate_identity_vaults_candidate_id",
        "candidate_identity_vaults",
        ["candidate_id"],
        unique=True,
    )
    op.create_index(
        "ix_candidate_identity_vaults_project_id", "candidate_identity_vaults", ["project_id"]
    )
    op.execute("ALTER TABLE candidate_identity_vaults ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE candidate_identity_vaults FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_candidate_identity_vaults ON candidate_identity_vaults
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON candidate_identity_vaults TO app_runtime")

    # --- identity_reveal_events ---------------------------------------------------------------
    op.create_table(
        "identity_reveal_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_identity_reveal_events_company_id", "identity_reveal_events", ["company_id"]
    )
    op.create_index(
        "ix_identity_reveal_events_candidate_id", "identity_reveal_events", ["candidate_id"]
    )
    op.create_index(
        "ix_identity_reveal_events_project_id", "identity_reveal_events", ["project_id"]
    )
    op.create_index(
        "ix_identity_reveal_events_actor_user_id", "identity_reveal_events", ["actor_user_id"]
    )
    op.execute("ALTER TABLE identity_reveal_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE identity_reveal_events FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_identity_reveal_events ON identity_reveal_events
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON identity_reveal_events TO app_runtime")

    # --- candidates: add callsign / candidate_ref, nullable for the backfill ------------------
    op.add_column("candidates", sa.Column("callsign", sa.String(50), nullable=True))
    op.add_column("candidates", sa.Column("candidate_ref", sa.String(30), nullable=True))

    # --- backfill ------------------------------------------------------------------------------
    conn = op.get_bind()
    used_callsigns: set[tuple[uuid.UUID, str]] = set()
    rows = conn.execute(
        sa.text(
            "SELECT id, company_id, project_id, full_name, email, phone, location, "
            "current_employer, current_title FROM candidates"
        )
    ).fetchall()

    for row in rows:
        callsign = _generate_callsign(used_callsigns, row.project_id)
        seq = conn.execute(sa.text("SELECT nextval('candidate_ref_seq')")).scalar_one()
        candidate_ref = f"PH-{datetime.now(timezone.utc).year}-{seq:04d}"

        conn.execute(
            sa.text(
                "INSERT INTO candidate_identity_vaults "
                "(id, company_id, candidate_id, project_id, full_name_encrypted, "
                "email_encrypted, phone_encrypted, location_encrypted, "
                "current_employer_encrypted, current_title_encrypted, deleted_at) "
                "VALUES (:id, :company_id, :candidate_id, :project_id, :full_name_encrypted, "
                ":email_encrypted, :phone_encrypted, :location_encrypted, "
                ":current_employer_encrypted, :current_title_encrypted, NULL)"
            ),
            {
                "id": uuid.uuid4(),
                "company_id": row.company_id,
                "candidate_id": row.id,
                "project_id": row.project_id,
                "full_name_encrypted": encrypt_secret(row.full_name or "Unknown Candidate"),
                "email_encrypted": encrypt_secret(row.email) if row.email else None,
                "phone_encrypted": encrypt_secret(row.phone) if row.phone else None,
                "location_encrypted": encrypt_secret(row.location) if row.location else None,
                "current_employer_encrypted": (
                    encrypt_secret(row.current_employer) if row.current_employer else None
                ),
                "current_title_encrypted": (
                    encrypt_secret(row.current_title) if row.current_title else None
                ),
            },
        )
        conn.execute(
            sa.text(
                "UPDATE candidates SET callsign = :callsign, candidate_ref = :ref WHERE id = :id"
            ),
            {"callsign": callsign, "ref": candidate_ref, "id": row.id},
        )

    op.alter_column("candidates", "callsign", nullable=False)
    op.alter_column("candidates", "candidate_ref", nullable=False)
    op.create_unique_constraint(
        "uq_candidates_project_callsign", "candidates", ["project_id", "callsign"]
    )
    op.create_unique_constraint("uq_candidates_candidate_ref", "candidates", ["candidate_ref"])

    # --- identity_vault.reveal permission, Owner only ------------------------------------------
    permission_id = uuid.uuid4()
    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        permissions_table,
        [
            {
                "id": permission_id,
                "code": "identity_vault.reveal",
                "description": "Reveal candidate identity from the vault",
            }
        ],
    )
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'Owner' AND p.code = 'identity_vault.reveal'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'identity_vault.reveal')
        """
    )
    op.execute("DELETE FROM permissions WHERE code = 'identity_vault.reveal'")

    op.drop_constraint("uq_candidates_candidate_ref", "candidates", type_="unique")
    op.drop_constraint("uq_candidates_project_callsign", "candidates", type_="unique")
    op.drop_column("candidates", "candidate_ref")
    op.drop_column("candidates", "callsign")

    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_identity_reveal_events ON identity_reveal_events"
    )
    op.execute("ALTER TABLE identity_reveal_events NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE identity_reveal_events DISABLE ROW LEVEL SECURITY")
    op.drop_table("identity_reveal_events")

    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_candidate_identity_vaults "
        "ON candidate_identity_vaults"
    )
    op.execute("ALTER TABLE candidate_identity_vaults NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE candidate_identity_vaults DISABLE ROW LEVEL SECURITY")
    op.drop_table("candidate_identity_vaults")

    op.execute("DROP SEQUENCE IF EXISTS candidate_ref_seq")
