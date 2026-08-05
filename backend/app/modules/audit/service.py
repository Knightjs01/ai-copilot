import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.repository import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = AuditRepository(session)

    async def record(
        self,
        *,
        company_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        action: str,
        target_type: str,
        target_id: uuid.UUID | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> None:
        await self._repository.create(
            company_id=company_id,
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            extra_data=extra_data or {},
        )
