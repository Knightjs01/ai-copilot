import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform_admin.models import PlatformAdmin


class PlatformAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, admin_id: uuid.UUID) -> PlatformAdmin | None:
        return await self._session.get(PlatformAdmin, admin_id)

    async def get_by_email(self, email: str) -> PlatformAdmin | None:
        result = await self._session.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == email)
        )
        return result.scalar_one_or_none()
