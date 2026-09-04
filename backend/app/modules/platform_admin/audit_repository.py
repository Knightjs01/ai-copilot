import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform_admin.audit_models import PlatformAdminAuditLog


class PlatformAdminAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        admin_id: uuid.UUID,
        action: str,
        target_type: str,
        target_id: uuid.UUID | None,
        extra_data: dict[str, Any],
    ) -> PlatformAdminAuditLog:
        entry = PlatformAdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            extra_data=extra_data,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_recent(self, *, limit: int = 50) -> list[PlatformAdminAuditLog]:
        result = await self._session.execute(
            select(PlatformAdminAuditLog)
            .order_by(PlatformAdminAuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_target(
        self, *, target_type: str, target_id: uuid.UUID, limit: int = 50
    ) -> list[PlatformAdminAuditLog]:
        result = await self._session.execute(
            select(PlatformAdminAuditLog)
            .where(
                PlatformAdminAuditLog.target_type == target_type,
                PlatformAdminAuditLog.target_id == target_id,
            )
            .order_by(PlatformAdminAuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        action: str | None = None,
        admin_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PlatformAdminAuditLog]:
        query = select(PlatformAdminAuditLog)
        if action is not None:
            query = query.where(PlatformAdminAuditLog.action == action)
        if admin_id is not None:
            query = query.where(PlatformAdminAuditLog.admin_id == admin_id)
        query = query.order_by(PlatformAdminAuditLog.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_all(
        self, *, action: str | None = None, admin_id: uuid.UUID | None = None
    ) -> int:
        query = select(func.count()).select_from(PlatformAdminAuditLog)
        if action is not None:
            query = query.where(PlatformAdminAuditLog.action == action)
        if admin_id is not None:
            query = query.where(PlatformAdminAuditLog.admin_id == admin_id)
        result = await self._session.execute(query)
        return result.scalar_one()
