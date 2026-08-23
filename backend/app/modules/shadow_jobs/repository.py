import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.shadow_jobs.models import ShadowApplication, ShadowJob, ShadowJobStatus


class ShadowJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        created_by_id: uuid.UUID,
        title: str,
        department: str | None,
        seniority: str | None,
        employment_type: str,
        location: str | None,
        remote_preference: str | None,
        salary_min: int | None,
        salary_max: int | None,
        summary: str,
        description: str,
        requirements: list[Any],
        project_id: uuid.UUID | None,
    ) -> ShadowJob:
        job = ShadowJob(
            company_id=company_id,
            created_by_id=created_by_id,
            title=title,
            department=department,
            seniority=seniority,
            employment_type=employment_type,
            location=location,
            remote_preference=remote_preference,
            salary_min=salary_min,
            salary_max=salary_max,
            summary=summary,
            description=description,
            requirements=requirements,
            project_id=project_id,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> ShadowJob | None:
        return await self._session.get(ShadowJob, job_id)

    async def get_by_project_id(self, project_id: uuid.UUID) -> ShadowJob | None:
        result = await self._session.execute(
            select(ShadowJob).where(ShadowJob.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def delete_by_id(self, job_id: uuid.UUID) -> None:
        await self._session.execute(delete(ShadowJob).where(ShadowJob.id == job_id))

    async def list_by_company(
        self, company_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[ShadowJob]:
        result = await self._session.execute(
            select(ShadowJob)
            .where(ShadowJob.company_id == company_id, ShadowJob.deleted_at.is_(None))
            .order_by(ShadowJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_published(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        seniority: str | None = None,
        remote_preference: str | None = None,
        employment_type: str | None = None,
        location: str | None = None,
    ) -> list[ShadowJob]:
        """Deliberately not filtered by company_id — the public board spans every company. Safe
        to run on the app_auth (BYPASSRLS) connection because every filter here is a status/
        attribute check, never something that could leak one company's private data to another."""

        query = select(ShadowJob).where(
            ShadowJob.status == ShadowJobStatus.PUBLISHED.value, ShadowJob.deleted_at.is_(None)
        )
        if seniority is not None:
            query = query.where(ShadowJob.seniority == seniority)
        if remote_preference is not None:
            query = query.where(ShadowJob.remote_preference == remote_preference)
        if employment_type is not None:
            query = query.where(ShadowJob.employment_type == employment_type)
        if location is not None:
            query = query.where(ShadowJob.location == location)
        query = query.order_by(ShadowJob.published_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class ShadowApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        shadow_job_id: uuid.UUID,
        candidate_user_id: uuid.UUID,
        phantom_passport_id: uuid.UUID,
        passport_version_id: uuid.UUID | None,
        callsign: str,
    ) -> ShadowApplication:
        application = ShadowApplication(
            company_id=company_id,
            shadow_job_id=shadow_job_id,
            candidate_user_id=candidate_user_id,
            phantom_passport_id=phantom_passport_id,
            passport_version_id=passport_version_id,
            callsign=callsign,
        )
        self._session.add(application)
        await self._session.flush()
        return application

    async def get_by_id(self, application_id: uuid.UUID) -> ShadowApplication | None:
        return await self._session.get(ShadowApplication, application_id)

    async def update_status(
        self, application: ShadowApplication, *, status: str
    ) -> ShadowApplication:
        application.status = status
        await self._session.flush()
        return application

    async def persist_revealed_identity(
        self,
        application: ShadowApplication,
        *,
        full_name: str | None,
        email: str | None,
        phone: str | None,
        career_entries: list[dict[str, Any]] | None = None,
    ) -> ShadowApplication:
        """Called exactly once, by ShadowRevealService on first successful reveal -- the
        idempotency check (has this already been persisted?) lives in the service, not here."""
        application.revealed_full_name = full_name
        application.revealed_email = email
        application.revealed_phone = phone
        application.revealed_career_entries = career_entries
        await self._session.flush()
        return application

    async def update_pipeline_stage(
        self, application: ShadowApplication, *, pipeline_stage: str
    ) -> ShadowApplication:
        application.pipeline_stage = pipeline_stage
        await self._session.flush()
        return application

    async def mark_viewed(self, application: ShadowApplication) -> ShadowApplication:
        """No-op if already viewed -- viewed_at is a first-viewed timestamp, never overwritten."""
        if application.viewed_at is None:
            application.viewed_at = datetime.now(timezone.utc)
            await self._session.flush()
        return application

    async def get_by_job_and_candidate(
        self, *, shadow_job_id: uuid.UUID, candidate_user_id: uuid.UUID
    ) -> ShadowApplication | None:
        result = await self._session.execute(
            select(ShadowApplication).where(
                ShadowApplication.shadow_job_id == shadow_job_id,
                ShadowApplication.candidate_user_id == candidate_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def callsign_exists_for_job(self, shadow_job_id: uuid.UUID, callsign: str) -> bool:
        result = await self._session.execute(
            select(func.count()).where(
                ShadowApplication.shadow_job_id == shadow_job_id,
                ShadowApplication.callsign == callsign,
            )
        )
        return result.scalar_one() > 0

    async def list_by_candidate(self, candidate_user_id: uuid.UUID) -> list[ShadowApplication]:
        result = await self._session.execute(
            select(ShadowApplication)
            .where(ShadowApplication.candidate_user_id == candidate_user_id)
            .order_by(ShadowApplication.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_company_id(self, company_id: uuid.UUID) -> list[ShadowApplication]:
        result = await self._session.execute(
            select(ShadowApplication)
            .where(ShadowApplication.company_id == company_id)
            .order_by(ShadowApplication.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_job(self, shadow_job_id: uuid.UUID) -> list[ShadowApplication]:
        result = await self._session.execute(
            select(ShadowApplication)
            .where(ShadowApplication.shadow_job_id == shadow_job_id)
            .order_by(ShadowApplication.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_job(self, shadow_job_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count()).where(ShadowApplication.shadow_job_id == shadow_job_id)
        )
        return result.scalar_one()

    async def delete_by_job_id(self, shadow_job_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(ShadowApplication).where(ShadowApplication.shadow_job_id == shadow_job_id)
        )
