import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Permission, Role, RolePermission, UserRole


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_role(self, *, company_id: uuid.UUID, name: str, is_system: bool) -> Role:
        role = Role(company_id=company_id, name=name, is_system=is_system)
        self._session.add(role)
        await self._session.flush()
        return role

    async def get_role_by_name(self, company_id: uuid.UUID, name: str) -> Role | None:
        result = await self._session.execute(
            select(Role).where(Role.company_id == company_id, Role.name == name)
        )
        return result.scalar_one_or_none()

    async def get_permission_by_code(self, code: str) -> Permission | None:
        result = await self._session.execute(select(Permission).where(Permission.code == code))
        return result.scalar_one_or_none()

    async def grant_permission(self, *, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        self._session.add(RolePermission(role_id=role_id, permission_id=permission_id))
        await self._session.flush()

    async def assign_role_to_user(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self._session.add(UserRole(user_id=user_id, role_id=role_id))
        await self._session.flush()

    async def remove_role_from_user(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        user_role = await self._session.get(UserRole, {"user_id": user_id, "role_id": role_id})
        if user_role is not None:
            await self._session.delete(user_role)
            await self._session.flush()

    async def get_roles_for_user(self, user_id: uuid.UUID) -> list[Role]:
        result = await self._session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_permission_codes_for_user(self, user_id: uuid.UUID) -> set[str]:
        result = await self._session.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
        )
        return set(result.scalars().all())
