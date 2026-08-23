import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.passport_matching.models import PassportJobMatch


class PassportJobMatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_passport_version_and_job(
        self, passport_version_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> PassportJobMatch | None:
        result = await self._session.execute(
            select(PassportJobMatch).where(
                PassportJobMatch.passport_version_id == passport_version_id,
                PassportJobMatch.shadow_job_id == shadow_job_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_passport_version_and_jobs(
        self, passport_version_id: uuid.UUID, shadow_job_ids: list[uuid.UUID]
    ) -> list[PassportJobMatch]:
        if not shadow_job_ids:
            return []
        result = await self._session.execute(
            select(PassportJobMatch).where(
                PassportJobMatch.passport_version_id == passport_version_id,
                PassportJobMatch.shadow_job_id.in_(shadow_job_ids),
            )
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        passport_version_id: uuid.UUID,
        shadow_job_id: uuid.UUID,
        company_id: uuid.UUID,
        match_tier: str,
        match_score: int,
        strengths: list[Any],
        gaps: list[Any],
        summary: str,
        dimension_breakdown: list[Any],
        shadow_job_updated_at: datetime,
        model_used: str,
        generated_at: datetime,
    ) -> PassportJobMatch:
        existing = await self.get_by_passport_version_and_job(passport_version_id, shadow_job_id)
        if existing is not None:
            existing.match_tier = match_tier
            existing.match_score = match_score
            existing.strengths = strengths
            existing.gaps = gaps
            existing.summary = summary
            existing.dimension_breakdown = dimension_breakdown
            existing.shadow_job_updated_at = shadow_job_updated_at
            existing.model_used = model_used
            existing.generated_at = generated_at
            await self._session.flush()
            return existing

        match = PassportJobMatch(
            passport_version_id=passport_version_id,
            shadow_job_id=shadow_job_id,
            company_id=company_id,
            match_tier=match_tier,
            match_score=match_score,
            strengths=strengths,
            gaps=gaps,
            summary=summary,
            dimension_breakdown=dimension_breakdown,
            shadow_job_updated_at=shadow_job_updated_at,
            model_used=model_used,
            generated_at=generated_at,
        )
        self._session.add(match)
        await self._session.flush()
        return match

    async def list_by_candidate_version_and_companies(
        self, *, passport_version_id: uuid.UUID, company_ids: list[uuid.UUID]
    ) -> list[PassportJobMatch]:
        """Powers the candidate's own 'Potential opportunities' list (Talent Memory Phase 3) --
        scoped to the candidate's CURRENT Passport version only (a stale version's cached match
        shouldn't surface, matches this module's existing 'never serve stale AI output silently'
        discipline) and to companies the candidate currently holds a granted Talent Pool
        relationship with."""
        if not company_ids:
            return []
        result = await self._session.execute(
            select(PassportJobMatch).where(
                PassportJobMatch.passport_version_id == passport_version_id,
                PassportJobMatch.company_id.in_(company_ids),
            )
        )
        return list(result.scalars().all())

    async def mark_candidate_notified(self, match_id: uuid.UUID) -> None:
        match = await self._session.get(PassportJobMatch, match_id)
        if match is not None:
            match.candidate_notified_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def delete_by_shadow_job_id(self, shadow_job_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(PassportJobMatch).where(PassportJobMatch.shadow_job_id == shadow_job_id)
        )
