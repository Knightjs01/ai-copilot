import uuid

from app.modules.auth.models import Role
from app.modules.auth.permissions import ROLE_PERMISSIONS
from app.modules.auth.repository.roles import RoleRepository


async def seed_system_roles(
    role_repository: RoleRepository, company_id: uuid.UUID
) -> dict[str, Role]:
    """Creates the 3 fixed system roles for a newly-signed-up company and grants each its
    permissions from the ROLE_PERMISSIONS registry. Requires the permissions catalog to already
    be populated (done once by the Phase 1 migration)."""

    roles: dict[str, Role] = {}
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = await role_repository.create_role(
            company_id=company_id, name=role_name, is_system=True
        )
        for code in permission_codes:
            permission = await role_repository.get_permission_by_code(code)
            if permission is None:
                raise RuntimeError(f"Permission catalog missing code {code!r} — run migrations")
            await role_repository.grant_permission(role_id=role.id, permission_id=permission.id)
        roles[role_name] = role
    return roles
