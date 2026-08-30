import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.shadow_introduction.models import IntroductionRequest, IntroductionRequestStatus


class IntroductionRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        candidate_user_id: uuid.UUID,
        shadow_job_id: uuid.UUID,
        requested_by_user_id: uuid.UUID,
        message: str | None,
    ) -> IntroductionRequest:
        request = IntroductionRequest(
            company_id=company_id,
            candidate_user_id=candidate_user_id,
            shadow_job_id=shadow_job_id,
            requested_by_user_id=requested_by_user_id,
            message=message,
        )
        self._session.add(request)
        await self._session.flush()
        return request

    async def get_by_id(self, request_id: uuid.UUID) -> IntroductionRequest | None:
        return await self._session.get(IntroductionRequest, request_id)

    async def get_active_by_triple(
        self, *, candidate_user_id: uuid.UUID, company_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> IntroductionRequest | None:
        """Powers the duplicate-request check -- a still-pending or already-accepted row for this
        exact (candidate, company, job) triple. A declined row is deliberately excluded: matching
        TalentPoolGrant's precedent, a decline doesn't permanently block a future fresh request."""
        result = await self._session.execute(
            select(IntroductionRequest).where(
                IntroductionRequest.candidate_user_id == candidate_user_id,
                IntroductionRequest.company_id == company_id,
                IntroductionRequest.shadow_job_id == shadow_job_id,
                IntroductionRequest.status.in_(
                    (IntroductionRequestStatus.PENDING.value, IntroductionRequestStatus.ACCEPTED.value)
                ),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_company_and_job(
        self, *, company_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> list[IntroductionRequest]:
        result = await self._session.execute(
            select(IntroductionRequest).where(
                IntroductionRequest.company_id == company_id,
                IntroductionRequest.shadow_job_id == shadow_job_id,
            )
        )
        return list(result.scalars().all())

    async def list_by_candidate_id(
        self, candidate_user_id: uuid.UUID
    ) -> list[IntroductionRequest]:
        result = await self._session.execute(
            select(IntroductionRequest)
            .where(IntroductionRequest.candidate_user_id == candidate_user_id)
            .order_by(IntroductionRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def respond(
        self,
        request: IntroductionRequest,
        *,
        approve: bool,
        resulting_application_id: uuid.UUID | None = None,
    ) -> IntroductionRequest:
        request.status = (
            IntroductionRequestStatus.ACCEPTED.value
            if approve
            else IntroductionRequestStatus.DECLINED.value
        )
        request.resulting_application_id = resulting_application_id if approve else None
        request.responded_at = datetime.now(timezone.utc)
        await self._session.flush()
        return request
