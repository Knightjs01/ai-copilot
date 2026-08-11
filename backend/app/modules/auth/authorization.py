"""Resource-level (ABAC) authorization helpers, layered on top of require_permission's
role-level check. Owner/Admin keep company-wide access — this only restricts Member-role
actors to the specific projects (and by extension, candidates) they've been added to via
ProjectMember. Kept separate from auth/dependencies.py to avoid a circular import with
app.modules.projects, which auth doesn't otherwise depend on."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.permissions import RoleName
from app.modules.auth.repository.roles import RoleRepository

_ORG_WIDE_ROLES = {RoleName.OWNER, RoleName.ADMIN}


async def actor_has_org_wide_access(session: AsyncSession, user_id: uuid.UUID) -> bool:
    """True for Owner/Admin — they bypass every project-membership check by design."""

    role_names = {role.name for role in await RoleRepository(session).get_roles_for_user(user_id)}
    return bool(role_names & _ORG_WIDE_ROLES)
