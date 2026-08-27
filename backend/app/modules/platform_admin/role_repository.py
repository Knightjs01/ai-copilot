import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform_admin.models import (
    PlatformAdminPermission,
    PlatformAdminRole,
    PlatformAdminRoleAssignment,
    PlatformAdminRolePermission,
)


class PlatformAdminRoleRepository:
    """Mirrors auth.repository.roles.RoleRepository method-for-method, against the parallel
    platform-admin RBAC tables (see platform_admin/models.py)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_role_by_name(self, name: str) -> PlatformAdminRole | None:
        result = await self._session.execute(
            select(PlatformAdminRole).where(PlatformAdminRole.name == name)
        )
        return result.scalar_one_or_none()

    async def assign_role_to_admin(self, *, admin_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self._session.add(PlatformAdminRoleAssignment(admin_id=admin_id, role_id=role_id))
        await self._session.flush()

    async def get_roles_for_admin(self, admin_id: uuid.UUID) -> list[PlatformAdminRole]:
        result = await self._session.execute(
            select(PlatformAdminRole)
            .join(
                PlatformAdminRoleAssignment,
                PlatformAdminRoleAssignment.role_id == PlatformAdminRole.id,
            )
            .where(PlatformAdminRoleAssignment.admin_id == admin_id)
        )
        return list(result.scalars().all())

    async def get_permission_codes_for_admin(self, admin_id: uuid.UUID) -> set[str]:
        result = await self._session.execute(
            select(PlatformAdminPermission.code)
            .join(
                PlatformAdminRolePermission,
                PlatformAdminRolePermission.permission_id == PlatformAdminPermission.id,
            )
            .join(
                PlatformAdminRoleAssignment,
                PlatformAdminRoleAssignment.role_id == PlatformAdminRolePermission.role_id,
            )
            .where(PlatformAdminRoleAssignment.admin_id == admin_id)
        )
        return set(result.scalars().all())
