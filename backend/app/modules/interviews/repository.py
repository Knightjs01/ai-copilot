import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.interviews.models import Interview


class InterviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        shadow_application_id: uuid.UUID,
        company_id: uuid.UUID,
        candidate_user_id: uuid.UUID,
        scheduled_at: datetime,
        location: str | None,
        meeting_link: str | None,
        scheduled_by_user_id: uuid.UUID,
    ) -> Interview:
        interview = Interview(
            shadow_application_id=shadow_application_id,
            company_id=company_id,
            candidate_user_id=candidate_user_id,
            scheduled_at=scheduled_at,
            location=location,
            meeting_link=meeting_link,
            scheduled_by_user_id=scheduled_by_user_id,
            status="scheduled",
        )
        self._session.add(interview)
        await self._session.flush()
        return interview

    async def get_by_id(self, interview_id: uuid.UUID) -> Interview | None:
        result = await self._session.execute(select(Interview).where(Interview.id == interview_id))
        return result.scalar_one_or_none()

    async def list_by_application_id(self, shadow_application_id: uuid.UUID) -> list[Interview]:
        result = await self._session.execute(
            select(Interview)
            .where(Interview.shadow_application_id == shadow_application_id)
            .order_by(Interview.scheduled_at)
        )
        return list(result.scalars().all())

    async def list_by_candidate_user_id(self, candidate_user_id: uuid.UUID) -> list[Interview]:
        result = await self._session.execute(
            select(Interview).where(Interview.candidate_user_id == candidate_user_id)
        )
        return list(result.scalars().all())

    async def list_upcoming_by_application_ids(
        self, shadow_application_ids: list[uuid.UUID]
    ) -> list[Interview]:
        """Bulk lookup used by ShadowJobService.list_applicants to populate
        ShadowProfile.has_upcoming_interview without a per-applicant round trip."""
        if not shadow_application_ids:
            return []
        result = await self._session.execute(
            select(Interview).where(
                Interview.shadow_application_id.in_(shadow_application_ids),
                Interview.status == "scheduled",
                Interview.scheduled_at > datetime.now(timezone.utc),
            )
        )
        return list(result.scalars().all())

    async def delete_by_shadow_application_ids(
        self, shadow_application_ids: list[uuid.UUID]
    ) -> None:
        if not shadow_application_ids:
            return
        await self._session.execute(
            delete(Interview).where(Interview.shadow_application_id.in_(shadow_application_ids))
        )
