"""Historic Project Vault: purged_project_records table (durable copy of each burn's
PurgeCertificate) and the historic_vault.view permission (Owner + Admin — the app's second
Owner/Admin-vs-Member divergence point, following identity_vault.reveal's Owner-only precedent).

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-06

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purged_project_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        # No ForeignKey — the project row this refers to is already gone by the time this row
        # exists (it's written moments before the project itself is deleted in the same burn).
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_title", sa.String(255), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("data_categories_destroyed", postgresql.JSONB(), nullable=False),
        sa.Column("purged_by_email", sa.String(320), nullable=False),
        sa.Column("purged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_purged_project_records_company_id", "purged_project_records", ["company_id"]
    )
    op.create_index(
        "ix_purged_project_records_project_id", "purged_project_records", ["project_id"]
    )
    op.execute("ALTER TABLE purged_project_records ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE purged_project_records FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_purged_project_records ON purged_project_records
        USING (company_id = current_setting('app.current_company_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON purged_project_records TO app_runtime")

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
                "code": "historic_vault.view",
                "description": "View purged project records and the company audit trail",
            }
        ],
    )
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name IN ('Owner', 'Admin') AND p.code = 'historic_vault.view'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM role_permissions
        WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'historic_vault.view')
        """
    )
    op.execute("DELETE FROM permissions WHERE code = 'historic_vault.view'")

    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_purged_project_records ON purged_project_records"
    )
    op.execute("ALTER TABLE purged_project_records NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE purged_project_records DISABLE ROW LEVEL SECURITY")
    op.drop_table("purged_project_records")
