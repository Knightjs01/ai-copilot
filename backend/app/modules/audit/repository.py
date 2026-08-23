import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.auth.models import User

_MAX_TARGET_ENTRIES = 100


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

    async def list_by_target(
        self, *, company_id: uuid.UUID, target_type: str, target_id: uuid.UUID
    ) -> list[tuple[AuditLog, str | None]]:
        """Left-joins the actor's current email -- a null actor_user_id (candidate-initiated
        rows, see e.g. shadow_reveal.approved/message.sent-from-candidate) or a since-removed
        user both fall back to None, same convention as historic_vault's company-wide read."""
        result = await self._session.execute(
            select(AuditLog, User.email)
            .outerjoin(User, User.id == AuditLog.actor_user_id)
            .where(
                AuditLog.company_id == company_id,
                AuditLog.target_type == target_type,
                AuditLog.target_id == target_id,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(_MAX_TARGET_ENTRIES)
        )
        return [(row[0], row[1]) for row in result.all()]
