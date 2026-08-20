import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.passport_matching.exceptions import (
    PassportMatchGenerationError,
    PassportNotApprovedError,
    ShadowJobNotFoundError,
    TooManyJobsRequestedError,
)
from app.modules.passport_matching.llm_client import (
    BoardFilterDraft,
    LLMRequestError,
    PassportMatchDraft,
    PassportMatchingLLMClient,
)
from app.modules.passport_matching.models import PassportJobMatch
from app.modules.passport_matching.repository import PassportJobMatchRepository
from app.modules.passport_matching.schemas import (
    BoardFilters,
    CandidateSearchCareerEntry,
    CandidateSearchResult,
    PassportJobMatchRead,
)
from app.modules.phantom_passport.repository import (
    PassportCareerEntryRepository,
    PassportVersionRepository,
    PhantomPassportRepository,
)
from app.modules.shadow_jobs.models import ShadowJob, ShadowJobStatus
from app.modules.shadow_jobs.repository import ShadowJobRepository

_MAX_BATCH_JOBS = 24
_MAX_SEARCH_RESULTS = 24
_COMPUTE_CONCURRENCY = 5


def _job_facts(job: ShadowJob) -> dict[str, object]:
    return {
        "title": job.title,
        "department": job.department,
        "seniority": job.seniority,
        "employment_type": job.employment_type,
        "location": job.location,
        "remote_preference": job.remote_preference,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "summary": job.summary,
        "description": job.description,
        "requirements": job.requirements,
    }


class PassportMatchingService:
    def __init__(
        self, session: AsyncSession, llm_client: PassportMatchingLLMClient | None = None
    ) -> None:
        self._settings = get_settings()
        self._matches = PassportJobMatchRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._versions = PassportVersionRepository(session)
        self._career_entries = PassportCareerEntryRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._llm_client = llm_client

    async def _resolve_approved_passport_version_id(self, candidate: CandidateUser) -> uuid.UUID:
        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None or passport.current_version_id is None:
            raise PassportNotApprovedError()
        return passport.current_version_id

    async def _score_via_llm(
        self, *, passport_snapshot: dict[str, Any], job: ShadowJob
    ) -> PassportMatchDraft:
        # Deliberately no DB access here — AsyncSession isn't safe for concurrent use across
        # coroutines, so every call that touches self._matches (an INSERT/UPDATE + flush) must
        # run sequentially. This method is the only part of a compute that batch_get_or_compute_
        # matches is allowed to run concurrently (see there); get_or_compute_match's single-job
        # path calls it directly since there's only ever one in flight.
        if self._llm_client is None:
            raise ValueError("compute requires an llm_client")
        try:
            return await self._llm_client.score_match(
                passport_snapshot=passport_snapshot, job_facts=_job_facts(job)
            )
        except LLMRequestError as exc:
            raise PassportMatchGenerationError(str(exc)) from exc

    async def _persist_match(
        self,
        *,
        passport_version_id: uuid.UUID,
        job: ShadowJob,
        draft: PassportMatchDraft,
    ) -> PassportJobMatch:
        return await self._matches.upsert(
            passport_version_id=passport_version_id,
            shadow_job_id=job.id,
            company_id=job.company_id,
            match_tier=draft.match_tier,
            match_score=draft.match_score,
            strengths=draft.strengths,
            gaps=draft.gaps,
            summary=draft.summary,
            shadow_job_updated_at=job.updated_at,
            model_used=self._settings.anthropic_model,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_or_compute_match(
        self, *, candidate: CandidateUser, shadow_job_id: uuid.UUID
    ) -> PassportJobMatchRead:
        passport_version_id = await self._resolve_approved_passport_version_id(candidate)

        job = await self._jobs.get_by_id(shadow_job_id)
        if (
            job is None
            or job.deleted_at is not None
            or job.status != ShadowJobStatus.PUBLISHED.value
        ):
            raise ShadowJobNotFoundError()

        cached = await self._matches.get_by_passport_version_and_job(passport_version_id, job.id)
        if cached is not None and cached.shadow_job_updated_at == job.updated_at:
            return self._to_read(cached)

        version = await self._versions.get_by_id(passport_version_id)
        assert version is not None  # current_version_id always points at a real, immutable row
        draft = await self._score_via_llm(passport_snapshot=version.snapshot, job=job)
        match = await self._persist_match(
            passport_version_id=passport_version_id, job=job, draft=draft
        )
        return self._to_read(match)

    async def batch_get_or_compute_matches(
        self, *, candidate: CandidateUser, shadow_job_ids: list[uuid.UUID]
    ) -> list[PassportJobMatchRead]:
        if len(shadow_job_ids) > _MAX_BATCH_JOBS:
            raise TooManyJobsRequestedError()

        passport_version_id = await self._resolve_approved_passport_version_id(candidate)

        jobs: list[ShadowJob] = []
        for job_id in shadow_job_ids:
            job = await self._jobs.get_by_id(job_id)
            if (
                job is not None
                and job.deleted_at is None
                and job.status == ShadowJobStatus.PUBLISHED.value
            ):
                jobs.append(job)
        if not jobs:
            return []

        cached_rows = await self._matches.list_by_passport_version_and_jobs(
            passport_version_id, [j.id for j in jobs]
        )
        cached_by_job = {row.shadow_job_id: row for row in cached_rows}

        fresh: dict[uuid.UUID, PassportJobMatch] = {}
        stale_jobs: list[ShadowJob] = []
        for job in jobs:
            cached = cached_by_job.get(job.id)
            if cached is not None and cached.shadow_job_updated_at == job.updated_at:
                fresh[job.id] = cached
            else:
                stale_jobs.append(job)

        if stale_jobs:
            version = await self._versions.get_by_id(passport_version_id)
            assert version is not None
            semaphore = asyncio.Semaphore(_COMPUTE_CONCURRENCY)

            async def _score_one(job: ShadowJob) -> tuple[ShadowJob, PassportMatchDraft | None]:
                # Only the LLM call runs concurrently -- the DB write happens afterward, back on
                # the main coroutine, one at a time (see _score_via_llm's docstring for why: a
                # shared AsyncSession can't safely INSERT/flush from multiple coroutines at once).
                async with semaphore:
                    try:
                        return job, await self._score_via_llm(
                            passport_snapshot=version.snapshot, job=job
                        )
                    except PassportMatchGenerationError:
                        # One job's score failing shouldn't blank out the whole board — skip it
                        # silently, same "fail open, no broken card" discipline the frontend
                        # applies to a candidate with no approved Passport at all.
                        return job, None

            scored = await asyncio.gather(*(_score_one(job) for job in stale_jobs))
            for job, draft in scored:
                if draft is not None:
                    row = await self._persist_match(
                        passport_version_id=passport_version_id, job=job, draft=draft
                    )
                    fresh[row.shadow_job_id] = row

        return [self._to_read(fresh[job.id]) for job in jobs if job.id in fresh]

    # --- Company side (candidate search) --------------------------------------------------------

    async def search_candidates_for_job(
        self, *, actor: User, job_id: uuid.UUID
    ) -> list[CandidateSearchResult]:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != actor.company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()

        candidates = await self._passports.list_discoverable_candidates()
        if not candidates:
            return []

        semaphore = asyncio.Semaphore(_COMPUTE_CONCURRENCY)

        async def _score_one(
            passport: Any,
        ) -> tuple[Any, PassportMatchDraft | None]:
            # Same "only the LLM call runs concurrently" discipline as batch_get_or_compute_
            # matches -- the DB write happens afterward, one at a time, back on the main
            # coroutine (see _score_via_llm's docstring).
            version = await self._versions.get_by_id(passport.current_version_id)
            if version is None:
                return passport, None
            async with semaphore:
                try:
                    return passport, await self._score_via_llm(
                        passport_snapshot=version.snapshot, job=job
                    )
                except PassportMatchGenerationError:
                    # One candidate's score failing shouldn't blank out the whole search --
                    # same "fail open" discipline as the batch match endpoint.
                    return passport, None

        scored = await asyncio.gather(*(_score_one(p) for p in candidates))

        results: list[CandidateSearchResult] = []
        for passport, draft in scored:
            if draft is None:
                continue
            match = await self._persist_match(
                passport_version_id=passport.current_version_id, job=job, draft=draft
            )
            career_entries = await self._career_entries.list_by_passport_id(passport.id)
            results.append(
                CandidateSearchResult(
                    callsign=passport.callsign or "Unknown",
                    headline=passport.headline,
                    seniority=passport.seniority,
                    years_experience=passport.years_experience,
                    summary=passport.summary,
                    skills=list(passport.skills),
                    industries=list(passport.industries),
                    location=passport.location,
                    remote_preference=passport.remote_preference,
                    salary_min=passport.salary_min,
                    salary_max=passport.salary_max,
                    notice_period=passport.notice_period,
                    career_intent=passport.career_intent,
                    career_entries=[
                        CandidateSearchCareerEntry(
                            title=entry.title,
                            company_name_anonymized=entry.company_name_anonymized,
                            is_current=entry.is_current,
                        )
                        for entry in career_entries
                    ],
                    match_tier=match.match_tier,  # type: ignore[arg-type]
                    match_score=match.match_score,
                    match_summary=match.summary,
                    strengths=match.strengths,
                    gaps=match.gaps,
                )
            )

        results.sort(key=lambda r: r.match_score, reverse=True)
        return results[:_MAX_SEARCH_RESULTS]

    async def parse_search_query(self, *, query: str) -> BoardFilters:
        if self._llm_client is None:
            raise ValueError("parse_search_query requires an llm_client")
        try:
            draft: BoardFilterDraft = await self._llm_client.parse_search_query(query=query)
        except LLMRequestError as exc:
            raise PassportMatchGenerationError(str(exc)) from exc
        return BoardFilters(
            seniority=draft.seniority,
            remote_preference=draft.remote_preference,
            employment_type=draft.employment_type,
            location=draft.location,
        )

    def _to_read(self, match: PassportJobMatch) -> PassportJobMatchRead:
        return PassportJobMatchRead(
            job_id=match.shadow_job_id,
            match_tier=match.match_tier,  # type: ignore[arg-type]
            match_score=match.match_score,
            strengths=match.strengths,
            gaps=match.gaps,
            summary=match.summary,
            generated_at=match.generated_at,
        )
