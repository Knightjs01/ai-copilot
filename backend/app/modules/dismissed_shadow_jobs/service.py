import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dismissed_shadow_jobs.exceptions import (
    DismissedJobNotFoundError,
    JobAlreadyDismissedError,
)
from app.modules.dismissed_shadow_jobs.repository import DismissedShadowJobRepository


class DismissedShadowJobService:
    def __init__(self, session: AsyncSession) -> None:
        self._dismissed = DismissedShadowJobRepository(session)

    async def dismiss_job(self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID) -> None:
        existing = await self._dismissed.get_by_candidate_and_job(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )
        if existing is not None:
            raise JobAlreadyDismissedError()
        await self._dismissed.create(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )

    async def undismiss_job(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> None:
        existing = await self._dismissed.get_by_candidate_and_job(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )
        if existing is None:
            raise DismissedJobNotFoundError()
        await self._dismissed.delete_by_candidate_and_job(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )

    async def list_dismissed_job_ids(self, candidate_user_id: uuid.UUID) -> list[uuid.UUID]:
        return await self._dismissed.list_job_ids_by_candidate(candidate_user_id)
