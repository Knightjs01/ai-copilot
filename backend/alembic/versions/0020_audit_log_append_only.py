"""Security: make audit_logs genuinely append-only at the DB privilege level

Prior to this, "append-only" was purely a code convention: no ORM path calls UPDATE/DELETE on
AuditLog, but both app_runtime and app_auth held full SELECT/INSERT/UPDATE/DELETE on this table
(app_runtime via 0001's blanket "GRANT ... ON ALL TABLES", app_auth the same way since
audit_logs existed before 0002 revoked app_auth's *default* privileges on future tables — that
revoke is not retroactive). Anyone with either connection string could silently rewrite or erase
the security audit trail. Revoking UPDATE/DELETE here means even a fully compromised application
connection cannot tamper with past entries — only INSERT (new entries) and SELECT (reading) work.

Revision ID: 0020
Revises: 0019
Create Date: 2026-08-12

"""

from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("REVOKE UPDATE, DELETE ON audit_logs FROM app_runtime")
    op.execute("REVOKE UPDATE, DELETE ON audit_logs FROM app_auth")


def downgrade() -> None:
    op.execute("GRANT UPDATE, DELETE ON audit_logs TO app_runtime")
    op.execute("GRANT UPDATE, DELETE ON audit_logs TO app_auth")
