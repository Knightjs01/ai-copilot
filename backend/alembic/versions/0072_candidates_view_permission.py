"""Phantom Command 2.0 Phase 4: a new candidates.view platform-admin permission, granted to the
same role set that already holds jobs.view -- Super Admin, Platform Admin, Reviewer, Analytics.
Deliberately excludes Support Admin, matching that role's existing "narrow by default, expand
once there's a real support workflow to gate" precedent (see the companies.create migration).

Revision ID: 0072
Revises: 0071
Create Date: 2026-09-04

"""

import uuid

from alembic import op

revision: str = "0072"
down_revision: str | None = "0071"
branch_labels = None
depends_on = None

_CODE = "candidates.view"
_DESCRIPTION = "View candidate Passports and their real application history"
_GRANTED_ROLES = ["Super Admin", "Platform Admin", "Reviewer", "Analytics"]


def upgrade() -> None:
    permission_id = uuid.uuid4()
    op.execute(
        f"""
        INSERT INTO platform_admin_permissions (id, code, description)
        VALUES ('{permission_id}'::uuid, '{_CODE}', '{_DESCRIPTION}')
        """
    )
    for role_name in _GRANTED_ROLES:
        op.execute(
            f"""
            INSERT INTO platform_admin_role_permissions (role_id, permission_id)
            SELECT r.id, '{permission_id}'::uuid
            FROM platform_admin_roles r
            WHERE r.name = '{role_name}'
            ON CONFLICT DO NOTHING
            """
        )


def downgrade() -> None:
    op.execute(
        f"DELETE FROM platform_admin_role_permissions WHERE permission_id IN "
        f"(SELECT id FROM platform_admin_permissions WHERE code = '{_CODE}')"
    )
    op.execute(f"DELETE FROM platform_admin_permissions WHERE code = '{_CODE}'")
