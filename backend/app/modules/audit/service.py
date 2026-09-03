import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import AuditEntryRead


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

    async def list_by_target(
        self, *, company_id: uuid.UUID, target_type: str, target_id: uuid.UUID
    ) -> list[AuditEntryRead]:
        rows = await self._repository.list_by_target(
            company_id=company_id, target_type=target_type, target_id=target_id
        )
        return [
            AuditEntryRead(
                id=entry.id,
                actor_email=actor_email,
                action=entry.action,
                target_type=entry.target_type,
                target_id=entry.target_id,
                extra_data=entry.extra_data,
                created_at=entry.created_at,
            )
            for entry, actor_email in rows
        ]

    async def list_by_company(
        self, *, company_id: uuid.UUID, limit: int = 100
    ) -> list[AuditEntryRead]:
        rows = await self._repository.list_by_company(company_id=company_id, limit=limit)
        return [
            AuditEntryRead(
                id=entry.id,
                actor_email=actor_email,
                action=entry.action,
                target_type=entry.target_type,
                target_id=entry.target_id,
                extra_data=entry.extra_data,
                created_at=entry.created_at,
            )
            for entry, actor_email in rows
        ]
