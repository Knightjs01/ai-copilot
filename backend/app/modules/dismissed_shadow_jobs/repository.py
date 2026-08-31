import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dismissed_shadow_jobs.models import DismissedShadowJob


class DismissedShadowJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> DismissedShadowJob:
        dismissed = DismissedShadowJob(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )
        self._session.add(dismissed)
        await self._session.flush()
        return dismissed

    async def get_by_candidate_and_job(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> DismissedShadowJob | None:
        result = await self._session.execute(
            select(DismissedShadowJob).where(
                DismissedShadowJob.candidate_user_id == candidate_user_id,
                DismissedShadowJob.shadow_job_id == shadow_job_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_job_ids_by_candidate(self, candidate_user_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(DismissedShadowJob.shadow_job_id).where(
                DismissedShadowJob.candidate_user_id == candidate_user_id
            )
        )
        return list(result.scalars().all())

    async def delete_by_candidate_and_job(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(DismissedShadowJob).where(
                DismissedShadowJob.candidate_user_id == candidate_user_id,
                DismissedShadowJob.shadow_job_id == shadow_job_id,
            )
        )
