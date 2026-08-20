import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.models import Company
from app.modules.saved_shadow_jobs.exceptions import (
    JobAlreadySavedError,
    SavedJobNotFoundError,
    ShadowJobNotFoundForSaveError,
)
from app.modules.saved_shadow_jobs.models import SavedShadowJob
from app.modules.saved_shadow_jobs.repository import SavedShadowJobRepository
from app.modules.saved_shadow_jobs.schemas import SavedShadowJobRead
from app.modules.shadow_jobs.models import ShadowJob, ShadowJobStatus
from app.modules.shadow_jobs.repository import ShadowJobRepository
from app.modules.shadow_jobs.schemas import ShadowJobBoardListing


class SavedShadowJobService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._saved = SavedShadowJobRepository(session)
        self._jobs = ShadowJobRepository(session)

    async def save_job(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID, collection_name: str | None
    ) -> SavedShadowJobRead:
        job = await self._jobs.get_by_id(shadow_job_id)
        if (
            job is None
            or job.deleted_at is not None
            or job.status != ShadowJobStatus.PUBLISHED.value
        ):
            raise ShadowJobNotFoundForSaveError()

        existing = await self._saved.get_by_candidate_and_job(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )
        if existing is not None:
            raise JobAlreadySavedError()

        saved = await self._saved.create(
            candidate_user_id=candidate_user_id,
            shadow_job_id=shadow_job_id,
            collection_name=collection_name,
        )
        return await self._to_read(saved, job)

    async def unsave_job(self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID) -> None:
        existing = await self._saved.get_by_candidate_and_job(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )
        if existing is None:
            raise SavedJobNotFoundError()
        await self._saved.delete_by_candidate_and_job(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )

    async def update_collection(
        self, *, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID, collection_name: str | None
    ) -> SavedShadowJobRead:
        saved = await self._saved.get_by_candidate_and_job(
            candidate_user_id=candidate_user_id, shadow_job_id=shadow_job_id
        )
        if saved is None:
            raise SavedJobNotFoundError()
        saved.collection_name = collection_name
        await self._session.flush()
        job = await self._jobs.get_by_id(shadow_job_id)
        if job is None:
            raise ShadowJobNotFoundForSaveError()
        return await self._to_read(saved, job)

    async def list_saved(
        self, *, candidate_user_id: uuid.UUID, collection_name: str | None = None
    ) -> list[SavedShadowJobRead]:
        saved_rows = await self._saved.list_by_candidate(
            candidate_user_id, collection_name=collection_name
        )
        results: list[SavedShadowJobRead] = []
        for saved in saved_rows:
            job = await self._jobs.get_by_id(saved.shadow_job_id)
            if job is None:
                # The underlying job row is gone (e.g. a project purge cascade) -- drop the
                # stale bookmark silently rather than surface a broken card.
                continue
            results.append(await self._to_read(saved, job))
        return results

    async def _to_read(self, saved: SavedShadowJob, job: ShadowJob) -> SavedShadowJobRead:
        company = await self._session.get(Company, job.company_id)
        listing = ShadowJobBoardListing(
            id=job.id,
            company_name=company.name if company else "Unknown company",
            company_slug=company.slug if company and company.is_profile_public else None,
            title=job.title,
            department=job.department,
            seniority=job.seniority,
            employment_type=job.employment_type,
            location=job.location,
            remote_preference=job.remote_preference,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            summary=job.summary,
            description=job.description,
            requirements=job.requirements,
            published_at=job.published_at,
        )
        return SavedShadowJobRead(
            id=saved.id,
            collection_name=saved.collection_name,
            created_at=saved.created_at,
            job=listing,
        )
