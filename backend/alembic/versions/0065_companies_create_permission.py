"""Company Onboarding Phase 1: a new companies.create platform-admin permission, granted only to
Super Admin -- deliberately narrower than companies.manage (held by the broader Platform Admin
role too), since originating a brand-new tenant + Owner is a bigger action than anything
companies.manage currently gates (suspend/verify/approve-profile on an already-existing company).

Revision ID: 0065
Revises: 0064
Create Date: 2026-08-28

"""

import uuid

from alembic import op

revision: str = "0065"
down_revision: str | None = "0064"
branch_labels = None
depends_on = None

_CODE = "companies.create"
_DESCRIPTION = (
    "Originate a brand-new company plus Owner with no prior access request, and author its "
    "initial Shadow profile before activation"
)
_GRANTED_ROLES = ["Super Admin"]


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
