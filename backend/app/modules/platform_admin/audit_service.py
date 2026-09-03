import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform_admin.audit_models import PlatformAdminAuditLog
from app.modules.platform_admin.audit_repository import PlatformAdminAuditRepository


class PlatformAdminAuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = PlatformAdminAuditRepository(session)

    async def record(
        self,
        *,
        admin_id: uuid.UUID,
        action: str,
        target_type: str,
        target_id: uuid.UUID | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> None:
        await self._repository.create(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            extra_data=extra_data or {},
        )

    async def list_recent(self, *, limit: int = 50) -> list[PlatformAdminAuditLog]:
        return await self._repository.list_recent(limit=limit)

    async def list_by_target(
        self, *, target_type: str, target_id: uuid.UUID, limit: int = 50
    ) -> list[PlatformAdminAuditLog]:
        return await self._repository.list_by_target(
            target_type=target_type, target_id=target_id, limit=limit
        )
