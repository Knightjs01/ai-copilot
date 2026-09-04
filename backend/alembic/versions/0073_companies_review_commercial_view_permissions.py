"""Phantom Command 2.0 Phase 5: two new finer-grained platform-admin permissions, splitting two
existing bundled codes -- companies.manage (governance suspend/reactivate/verify/unverify vs.
one-time review decisions) and commercial.manage (a read-only catalog view vs. the actual plan
change). Both new codes are purely additive: no existing grant is removed from any role.

companies.review lets Reviewer approve/reject a pending company profile review or access request
-- a real gap, since Reviewer already had the equivalent split for jobs (jobs.view/jobs.review)
but never got it for companies. commercial.view lets Analytics (the platform's read-only role)
see the commercial plan catalog, matching its "read everything" purpose.

Revision ID: 0073
Revises: 0072
Create Date: 2026-09-04

"""

import uuid

from alembic import op

revision: str = "0073"
down_revision: str | None = "0072"
branch_labels = None
depends_on = None

_PERMISSIONS = [
    (
        "companies.review",
        "Approve or reject a pending company profile review or access request",
        ["Super Admin", "Platform Admin", "Reviewer"],
    ),
    (
        "commercial.view",
        "View the commercial plan catalog",
        ["Super Admin", "Platform Admin", "Analytics"],
    ),
]


def upgrade() -> None:
    for code, description, granted_roles in _PERMISSIONS:
        permission_id = uuid.uuid4()
        op.execute(
            f"""
            INSERT INTO platform_admin_permissions (id, code, description)
            VALUES ('{permission_id}'::uuid, '{code}', '{description}')
            """
        )
        for role_name in granted_roles:
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
    for code, _description, _granted_roles in _PERMISSIONS:
        op.execute(
            f"DELETE FROM platform_admin_role_permissions WHERE permission_id IN "
            f"(SELECT id FROM platform_admin_permissions WHERE code = '{code}')"
        )
        op.execute(f"DELETE FROM platform_admin_permissions WHERE code = '{code}'")
