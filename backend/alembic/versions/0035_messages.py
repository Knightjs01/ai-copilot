"""Messages: message_threads + messages, candidate <-> company messaging scoped to a Shadow
application. Structurally dual-audience like shadow_jobs/shadow_reveal/passport_matching:
message_threads carries company_id for RLS on the company path, plus an explicit GRANT to
app_auth for the candidate path (which always bypasses RLS via get_db, filtered explicitly by
candidate_user_id in the repository — never trust RLS for that side, same rationale migration
0017 documents). messages.thread_id FKs with ON DELETE CASCADE so a project purge only needs to
delete message_threads rows for the purged applications.

New permissions messages.view (Owner+Admin+Member) and messages.send (Owner+Admin) — mirrors the
exact split already established for shadow_jobs itself (view is team-wide, mutations are
Owner+Admin only), the feature area this module is directly attached to.

Revision ID: 0035
Revises: 0034
Create Date: 2026-08-18

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0035"
down_revision: str | None = "0034"
branch_labels = None
depends_on = None

_NEW_PERMISSIONS = [
    (uuid.uuid4(), "messages.view", "View candidate/company message threads on Shadow applications"),
    (uuid.uuid4(), "messages.send", "Send messages to a Shadow applicant"),
]
_OWNER_AND_ADMIN_CODES = ["messages.view", "messages.send"]
_MEMBER_CODES = ["messages.view"]


def upgrade() -> None:
    op.create_table(
        "message_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "shadow_application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shadow_applications.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column(
            "candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=False,
        ),
        sa.Column("candidate_last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("company_last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_message_threads_company_id", "message_threads", ["company_id"])
    op.create_index(
        "ix_message_threads_candidate_user_id", "message_threads", ["candidate_user_id"]
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "thread_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("message_threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_type", sa.String(20), nullable=False),
        sa.Column(
            "sender_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "sender_candidate_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_users.id"),
            nullable=True,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"])

    op.execute("ALTER TABLE message_threads ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE message_threads FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_message_threads ON message_threads
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON message_threads, messages TO app_runtime, app_auth"
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

    op.execute("DROP POLICY IF EXISTS tenant_isolation_message_threads ON message_threads")
    op.execute("ALTER TABLE message_threads NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE message_threads DISABLE ROW LEVEL SECURITY")
    op.drop_table("messages")
    op.drop_table("message_threads")
