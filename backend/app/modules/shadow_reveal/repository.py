import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.shadow_jobs.models import ShadowApplication
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
        disclosed_fields: list[str] | None = None,
    ) -> ShadowRevealRequest:
        request.status = (
            RevealRequestStatus.APPROVED.value if approve else RevealRequestStatus.DECLINED.value
        )
        request.disclosure_level = disclosure_level if approve else None
        request.disclosed_fields = disclosed_fields if approve else None
        request.responded_at = datetime.now(timezone.utc)
        await self._session.flush()
        return request

    async def mark_company_viewed(self, request: ShadowRevealRequest) -> ShadowRevealRequest:
        """No-op if already viewed -- company_viewed_at is a first-viewed-since-response
        timestamp, never overwritten (mirrors ShadowApplicationRepository.mark_viewed)."""
        if request.company_viewed_at is None:
            request.company_viewed_at = datetime.now(timezone.utc)
            await self._session.flush()
        return request

    async def list_by_application_ids(
        self, application_ids: list[uuid.UUID]
    ) -> list[ShadowRevealRequest]:
        """Bulk lookup for the applicant list -- one query for the whole board, not one per
        card. Powers ShadowProfile.reveal_response_is_new, same shape as
        ShadowJobService._unread_counts_for_applications."""
        if not application_ids:
            return []
        result = await self._session.execute(
            select(ShadowRevealRequest).where(
                ShadowRevealRequest.shadow_application_id.in_(application_ids)
            )
        )
        return list(result.scalars().all())

    async def list_unseen_responses_by_company(
        self, company_id: uuid.UUID
    ) -> list[ShadowRevealRequest]:
        """Every reveal request this company has responded to (approved/declined) that nobody
        has opened the applicant's card for since -- powers the dashboard action item."""
        result = await self._session.execute(
            select(ShadowRevealRequest).where(
                ShadowRevealRequest.company_id == company_id,
                ShadowRevealRequest.status != RevealRequestStatus.PENDING.value,
                ShadowRevealRequest.company_viewed_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def list_by_candidate_id(self, candidate_user_id: uuid.UUID) -> list[ShadowRevealRequest]:
        """Every reveal request/response across every application this candidate has ever
        submitted, newest first -- powers the candidate-wide Identity Activity view. Joins
        through ShadowApplication since ShadowRevealRequest has no candidate_user_id column of
        its own (a request is scoped to one application, not one candidate directly)."""
        result = await self._session.execute(
            select(ShadowRevealRequest)
            .join(
                ShadowApplication,
                ShadowRevealRequest.shadow_application_id == ShadowApplication.id,
            )
            .where(ShadowApplication.candidate_user_id == candidate_user_id)
            .order_by(ShadowRevealRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_by_application_ids(self, application_ids: list[uuid.UUID]) -> None:
        if not application_ids:
            return
        await self._session.execute(
            delete(ShadowRevealRequest).where(
                ShadowRevealRequest.shadow_application_id.in_(application_ids)
            )
        )
