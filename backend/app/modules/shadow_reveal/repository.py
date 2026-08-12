import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.shadow_reveal.models import RevealRequestStatus, ShadowRevealRequest


class ShadowRevealRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        shadow_application_id: uuid.UUID,
        requested_by_user_id: uuid.UUID,
        reason: str | None,
    ) -> ShadowRevealRequest:
        request = ShadowRevealRequest(
            company_id=company_id,
            shadow_application_id=shadow_application_id,
            requested_by_user_id=requested_by_user_id,
            reason=reason,
        )
        self._session.add(request)
        await self._session.flush()
        return request

    async def get_by_id(self, request_id: uuid.UUID) -> ShadowRevealRequest | None:
        return await self._session.get(ShadowRevealRequest, request_id)

    async def get_by_application_id(
        self, shadow_application_id: uuid.UUID
    ) -> ShadowRevealRequest | None:
        result = await self._session.execute(
            select(ShadowRevealRequest).where(
                ShadowRevealRequest.shadow_application_id == shadow_application_id
            )
        )
        return result.scalar_one_or_none()

    async def respond(
        self,
        request: ShadowRevealRequest,
        *,
        approve: bool,
        disclosure_level: str | None = None,
    ) -> ShadowRevealRequest:
        request.status = (
            RevealRequestStatus.APPROVED.value if approve else RevealRequestStatus.DECLINED.value
        )
        request.disclosure_level = disclosure_level if approve else None
        request.responded_at = datetime.now(timezone.utc)
        await self._session.flush()
        return request

    async def delete_by_application_ids(self, application_ids: list[uuid.UUID]) -> None:
        if not application_ids:
            return
        await self._session.execute(
            delete(ShadowRevealRequest).where(
                ShadowRevealRequest.shadow_application_id.in_(application_ids)
            )
        )
