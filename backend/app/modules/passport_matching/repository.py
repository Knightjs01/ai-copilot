import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.passport_matching.models import CandidatePass, PassportJobMatch


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

    async def count_by_shadow_job_id(self, shadow_job_id: uuid.UUID) -> int:
        """How many candidates already have a computed match for this job -- not a total
        addressable count, since matches are computed lazily as candidates/recruiters interact
        with the job, not for every discoverable candidate up front."""
        result = await self._session.execute(
            select(func.count()).where(PassportJobMatch.shadow_job_id == shadow_job_id)
        )
        return result.scalar_one()

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


class CandidatePassRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        candidate_user_id: uuid.UUID,
        shadow_job_id: uuid.UUID | None,
        reason: str | None,
        actor_user_id: uuid.UUID,
    ) -> CandidatePass:
        pass_row = CandidatePass(
            company_id=company_id,
            candidate_user_id=candidate_user_id,
            shadow_job_id=shadow_job_id,
            reason=reason,
            actor_user_id=actor_user_id,
        )
        self._session.add(pass_row)
        await self._session.flush()
        return pass_row

    async def list_by_company_id(self, company_id: uuid.UUID) -> list[CandidatePass]:
        result = await self._session.execute(
            select(CandidatePass).where(CandidatePass.company_id == company_id)
        )
        return list(result.scalars().all())

    async def is_passed_for_job(
        self, *, company_id: uuid.UUID, candidate_user_id: uuid.UUID, shadow_job_id: uuid.UUID
    ) -> bool:
        """True if this company passed on this candidate generally (job_id NULL) or for this
        specific job -- used to exclude them from search_candidates_for_job's result set."""
        result = await self._session.execute(
            select(CandidatePass.id).where(
                CandidatePass.company_id == company_id,
                CandidatePass.candidate_user_id == candidate_user_id,
                or_(
                    CandidatePass.shadow_job_id.is_(None),
                    CandidatePass.shadow_job_id == shadow_job_id,
                ),
            )
        )
        return result.scalar_one_or_none() is not None
