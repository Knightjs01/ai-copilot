import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.saved_shadow_jobs.models import SavedShadowJob


class SavedShadowJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID, collection_name: str | None
    ) -> SavedShadowJob:
        saved = SavedShadowJob(
            candidate_user_id=candidate_user_id,
            shadow_job_id=shadow_job_id,
            collection_name=collection_name,
        )
        self._session.add(saved)
        await self._session.flush()
        return saved

    async def get_by_candidate_and_job(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> SavedShadowJob | None:
        result = await self._session.execute(
            select(SavedShadowJob).where(
                SavedShadowJob.candidate_user_id == candidate_user_id,
                SavedShadowJob.shadow_job_id == shadow_job_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_candidate(
        self, candidate_user_id: uuid.UUID, *, collection_name: str | None = None
    ) -> list[SavedShadowJob]:
        query = select(SavedShadowJob).where(SavedShadowJob.candidate_user_id == candidate_user_id)
        if collection_name is not None:
            query = query.where(SavedShadowJob.collection_name == collection_name)
        query = query.order_by(SavedShadowJob.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def delete_by_candidate_and_job(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(SavedShadowJob).where(
                SavedShadowJob.candidate_user_id == candidate_user_id,
                SavedShadowJob.shadow_job_id == shadow_job_id,
            )
        )
