import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        action: str,
        target_type: str,
        target_id: uuid.UUID | None,
        extra_data: dict[str, Any],
    ) -> AuditLog:
        entry = AuditLog(
            company_id=company_id,
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            extra_data=extra_data,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
