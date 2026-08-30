import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import AuditService
from app.modules.auth.email import EmailSender, build_talent_pool_match_email
from app.modules.auth.models import User
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.repository import CandidateUserRepository
from app.modules.companies.models import Company
from app.modules.hiring_blueprint.models import HiringBlueprint
from app.modules.hiring_blueprint.repository import HiringBlueprintRepository
from app.modules.hiring_manager_alignment.models import HiringManagerAlignment
from app.modules.hiring_manager_alignment.repository import HiringManagerAlignmentRepository
from app.modules.passport_matching.exceptions import (
    ApplicationHasNoPassportVersionError,
    ApplicationNotFoundError,
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
from app.modules.passport_matching.models import CandidatePass, PassportJobMatch
from app.modules.passport_matching.repository import (
    CandidatePassRepository,
    PassportJobMatchRepository,
)
from app.modules.passport_matching.schemas import (
    BoardFilters,
    CandidateSearchCareerEntry,
    CandidateSearchResult,
    PassportJobMatchRead,
    PassReason,
    RelationshipStatus,
    TalentPoolMatchResult,
    TalentPoolOpportunity,
)
from app.modules.phantom_passport.repository import (
    PassportCareerEntryRepository,
    PassportVersionRepository,
    PhantomPassportRepository,
)
from app.modules.shadow_jobs.models import ShadowJob, ShadowJobStatus
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository
from app.modules.talent_pool.models import TalentPoolGrant, TalentPoolScope
from app.modules.talent_pool.repository import TalentPoolGrantRepository

logger = logging.getLogger("app.passport_matching.service")

_MAX_BATCH_JOBS = 24
_MAX_SEARCH_RESULTS = 24
_COMPUTE_CONCURRENCY = 5
_NOTIFY_MIN_TIER = {"Excellent Match", "Strong Match", "Potential Match"}

_LLM_DIMENSION_LABELS: dict[str, str] = {
    "role_alignment": "Role alignment",
    "industry_experience": "Industry experience",
    "functional_experience": "Functional experience",
}
# Fixed display order for the merged breakdown -- must match DimensionRating consumers on the
# frontend (Match tab renders in this exact order).
_DIMENSION_ORDER = [
    "Role alignment",
    "Industry experience",
    "Functional experience",
    "Seniority",
    "Location",
    "Compensation",
]


def _deterministic_dimensions(
    passport_snapshot: dict[str, Any], job: ShadowJob
) -> list[dict[str, str]]:
    """Location/Compensation/Seniority -- computed from real, on-file values only, zero LLM
    involvement, zero variance run-to-run. 'Moderate' always means one side is genuinely unstated,
    never a guess; every rating is traceable to the two actual values named in its evidence."""
    dimensions: list[dict[str, str]] = []

    # --- Location ---
    candidate_location = passport_snapshot.get("location")
    candidate_remote = passport_snapshot.get("remote_preference")
    job_location = job.location
    job_remote = job.remote_preference
    if job_remote == "remote" or candidate_remote == "remote":
        rating = "Strong"
        if job_remote == "remote":
            evidence = (
                f"Job is fully remote (candidate location: {candidate_location or 'not stated'})"
            )
        else:
            evidence = f"Candidate's remote preference is fully remote (job location: {job_location or 'not stated'})"
    elif job_location and candidate_location:
        rating = (
            "Strong"
            if job_location.strip().lower() == candidate_location.strip().lower()
            else "Weak"
        )
        evidence = f"Job requires {job_location}; candidate is based in {candidate_location}"
    else:
        rating = "Moderate"
        evidence = f"Job location: {job_location or 'not stated'}; candidate location: {candidate_location or 'not stated'}"
    dimensions.append({"dimension": "Location", "rating": rating, "evidence": evidence})

    # --- Compensation ---
    job_min, job_max = job.salary_min, job.salary_max
    cand_min, cand_max = passport_snapshot.get("salary_min"), passport_snapshot.get("salary_max")
    if job_min is not None and job_max is not None and cand_min is not None:
        overlaps = cand_min <= job_max and (cand_max is None or cand_max >= job_min)
        rating = "Strong" if overlaps else "Weak"
        cand_range = f"£{cand_min:,}" + (f"–£{cand_max:,}" if cand_max else "+")
        evidence = f"Job offers £{job_min:,}–£{job_max:,}; candidate expects {cand_range}"
    else:
        rating = "Moderate"
        evidence = "Salary range not fully stated on one side"
    dimensions.append({"dimension": "Compensation", "rating": rating, "evidence": evidence})

    # --- Seniority ---
    job_seniority = job.seniority
    cand_seniority = passport_snapshot.get("seniority")
    if job_seniority and cand_seniority:
        rating = (
            "Strong" if job_seniority.strip().lower() == cand_seniority.strip().lower() else "Weak"
        )
        evidence = f"Job seniority: {job_seniority}; candidate seniority: {cand_seniority}"
    else:
        rating = "Moderate"
        evidence = f"Job seniority: {job_seniority or 'not stated'}; candidate seniority: {cand_seniority or 'not stated'}"
    dimensions.append({"dimension": "Seniority", "rating": rating, "evidence": evidence})

    return dimensions


def _merge_dimension_breakdown(
    llm_dimensions: dict[str, dict[str, str]],
    passport_snapshot: dict[str, Any],
    job: ShadowJob,
) -> list[dict[str, str]]:
    by_name: dict[str, dict[str, str]] = {}
    for key, label in _LLM_DIMENSION_LABELS.items():
        entry = llm_dimensions.get(key)
        if entry is not None:
            by_name[label] = {"rating": entry["rating"], "evidence": entry["evidence"]}
    for dim in _deterministic_dimensions(passport_snapshot, job):
        by_name[dim["dimension"]] = {"rating": dim["rating"], "evidence": dim["evidence"]}
    return [{"dimension": name, **by_name[name]} for name in _DIMENSION_ORDER if name in by_name]


def _job_facts(
    job: ShadowJob,
    *,
    blueprint: HiringBlueprint | None = None,
    alignment: HiringManagerAlignment | None = None,
) -> dict[str, object]:
    facts: dict[str, object] = {
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
    # Only populated when this Shadow job is linked to an ATS project that has a real Hiring
    # Blueprint/Hiring Manager Alignment -- the common case (an unlinked job) behaves exactly as
    # before. Mirrors prescreen_assessment's real, already-shipped "smart fit" signal, extended
    # to the Shadow-side matching pool.
    if blueprint is not None:
        facts["role_summary"] = blueprint.role_summary
        facts["must_have_qualifications"] = blueprint.must_have_qualifications
    if alignment is not None:
        facts["top_requirements"] = alignment.top_requirements
    return facts


class PassportMatchingService:
    def __init__(
        self,
        session: AsyncSession,
        llm_client: PassportMatchingLLMClient | None = None,
        *,
        email_sender: EmailSender | None = None,
    ) -> None:
        self._session = session
        self._settings = get_settings()
        self._matches = PassportJobMatchRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._versions = PassportVersionRepository(session)
        self._career_entries = PassportCareerEntryRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._applications = ShadowApplicationRepository(session)
        self._blueprints = HiringBlueprintRepository(session)
        self._alignments = HiringManagerAlignmentRepository(session)
        self._talent_pool_grants = TalentPoolGrantRepository(session)
        self._candidate_users = CandidateUserRepository(session)
        self._passes = CandidatePassRepository(session)
        self._audit = AuditService(session)
        self._llm_client = llm_client
        self._email_sender = email_sender

    async def _resolve_approved_passport_version_id(self, candidate: CandidateUser) -> uuid.UUID:
        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None or passport.current_version_id is None:
            raise PassportNotApprovedError()
        return passport.current_version_id

    async def _score_via_llm(
        self,
        *,
        passport_snapshot: dict[str, Any],
        job: ShadowJob,
        blueprint: HiringBlueprint | None = None,
        alignment: HiringManagerAlignment | None = None,
    ) -> PassportMatchDraft:
        # Deliberately no DB access here — AsyncSession isn't safe for concurrent use across
        # coroutines, so every call that touches self._matches (an INSERT/UPDATE + flush) must
        # run sequentially. This method is the only part of a compute that batch_get_or_compute_
        # matches is allowed to run concurrently (see there); get_or_compute_match's single-job
        # path calls it directly since there's only ever one in flight.
        #
        # blueprint/alignment are pre-resolved by the caller, never looked up in here: this
        # method is shared by both the candidate-facing paths (get_or_compute_match,
        # batch_get_or_compute_matches — running on the RLS-bypass app_auth role via get_db) and
        # the company-facing search_candidates_for_job (app_runtime via get_tenant_db).
        # hiring_blueprints/hiring_manager_alignments are deliberately GRANTed to app_runtime
        # only (confirmed in 0006_hiring_blueprints.py/0007_hiring_manager_alignments.py) — a
        # candidate-facing session genuinely cannot read them, by design, unlike shadow_jobs
        # (explicitly GRANTed to both roles since job postings are meant to be public). Only
        # search_candidates_for_job resolves and passes these; the candidate-facing callers pass
        # neither, so their behavior is byte-for-byte unchanged.
        if self._llm_client is None:
            raise ValueError("compute requires an llm_client")
        try:
            return await self._llm_client.score_match(
                passport_snapshot=passport_snapshot,
                job_facts=_job_facts(job, blueprint=blueprint, alignment=alignment),
            )
        except LLMRequestError as exc:
            raise PassportMatchGenerationError(str(exc)) from exc

    async def _persist_match(
        self,
        *,
        passport_version_id: uuid.UUID,
        job: ShadowJob,
        passport_snapshot: dict[str, Any],
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
            dimension_breakdown=_merge_dimension_breakdown(
                draft.dimension_breakdown, passport_snapshot, job
            ),
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
            passport_version_id=passport_version_id,
            job=job,
            passport_snapshot=version.snapshot,
            draft=draft,
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
                        passport_version_id=passport_version_id,
                        job=job,
                        passport_snapshot=version.snapshot,
                        draft=draft,
                    )
                    fresh[row.shadow_job_id] = row

        return [self._to_read(fresh[job.id]) for job in jobs if job.id in fresh]

    # --- Company side (single applicant, already applied) -----------------------------------------

    async def get_or_compute_match_for_applicant(
        self, *, actor: User, job_id: uuid.UUID, application_id: uuid.UUID
    ) -> PassportJobMatchRead:
        """Company-side sibling of get_or_compute_match -- scores the one applicant already on
        this page against the job they applied to, using the passport_version_id frozen on their
        ShadowApplication at apply time (never their live, possibly-since-edited Passport), same
        "frozen snapshot" discipline _to_shadow_profile already applies everywhere else a company
        views an applicant."""
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != actor.company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()

        application = await self._applications.get_by_id(application_id)
        if application is None or application.shadow_job_id != job_id:
            raise ApplicationNotFoundError()
        if application.passport_version_id is None:
            raise ApplicationHasNoPassportVersionError()

        cached = await self._matches.get_by_passport_version_and_job(
            application.passport_version_id, job.id
        )
        if cached is not None and cached.shadow_job_updated_at == job.updated_at:
            return self._to_read(cached)

        blueprint: HiringBlueprint | None = None
        alignment: HiringManagerAlignment | None = None
        if job.project_id is not None:
            blueprint = await self._blueprints.get_by_project_id(job.project_id)
            alignment = await self._alignments.get_by_project_id(job.project_id)

        version = await self._versions.get_by_id(application.passport_version_id)
        if version is None:
            raise ApplicationHasNoPassportVersionError()
        draft = await self._score_via_llm(
            passport_snapshot=version.snapshot, job=job, blueprint=blueprint, alignment=alignment
        )
        match = await self._persist_match(
            passport_version_id=application.passport_version_id,
            job=job,
            passport_snapshot=version.snapshot,
            draft=draft,
        )
        return self._to_read(match)

    # --- Company side (candidate search) --------------------------------------------------------

    _ACTIVE_PIPELINE_STAGES = {"screening", "interviewing", "offer"}

    async def _compute_relationship_statuses(
        self,
        *,
        company_id: uuid.UUID,
        shadow_job_id: uuid.UUID,
        passes: list[CandidatePass],
    ) -> dict[uuid.UUID, RelationshipStatus]:
        """One candidate_user_id -> RelationshipStatus map for every real signal this company
        already has, computed once per search rather than once per candidate (avoids N+1 queries
        across up to 24 results). Priority: currently_engaged > in_talent_pool >
        previously_passed > previously_applied > new (the "new" default is never written here,
        just the absence of a key). `passes` is passed in rather than fetched here since the
        caller also needs the raw list to build its own exclusion set."""
        applications = await self._applications.list_by_company_id(company_id)
        grants = await self._talent_pool_grants.list_granted_by_company_id(company_id)

        statuses: dict[uuid.UUID, RelationshipStatus] = {}
        for application in applications:
            statuses[application.candidate_user_id] = "previously_applied"
        for pass_row in passes:
            if pass_row.shadow_job_id is None or pass_row.shadow_job_id == shadow_job_id:
                statuses[pass_row.candidate_user_id] = "previously_passed"
        for grant in grants:
            statuses[grant.candidate_user_id] = "in_talent_pool"
        for application in applications:
            if application.pipeline_stage in self._ACTIVE_PIPELINE_STAGES:
                statuses[application.candidate_user_id] = "currently_engaged"
        return statuses

    async def pass_candidate(
        self,
        *,
        actor: User,
        callsign: str,
        shadow_job_id: uuid.UUID | None,
        reason: PassReason | None,
    ) -> None:
        passport = await self._passports.get_by_callsign(callsign)
        if passport is None:
            raise ShadowJobNotFoundError()
        pass_row = await self._passes.create(
            company_id=actor.company_id,
            candidate_user_id=passport.candidate_user_id,
            shadow_job_id=shadow_job_id,
            reason=reason,
            actor_user_id=actor.id,
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="shadow_candidate.passed",
            target_type="candidate_pass",
            target_id=pass_row.id,
            extra_data={"reason": reason, "shadow_job_id": str(shadow_job_id) if shadow_job_id else None},
        )

    async def search_candidates_for_job(
        self, *, actor: User, job_id: uuid.UUID
    ) -> list[CandidateSearchResult]:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != actor.company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()

        candidates = await self._passports.list_discoverable_candidates()
        if not candidates:
            return []

        passes = await self._passes.list_by_company_id(actor.company_id)
        excluded_candidate_ids = {
            p.candidate_user_id
            for p in passes
            if p.shadow_job_id is None or p.shadow_job_id == job_id
        }
        candidates = [c for c in candidates if c.candidate_user_id not in excluded_candidate_ids]
        if not candidates:
            return []

        relationship_statuses = await self._compute_relationship_statuses(
            company_id=actor.company_id, shadow_job_id=job_id, passes=passes
        )

        # Resolved once per job (not per candidate) -- this method runs on app_runtime
        # (get_tenant_db), the one passport_matching call path actually permitted to read these
        # tenant-scoped tables. See _score_via_llm's docstring for why this can't also happen on
        # the candidate-facing paths.
        blueprint: HiringBlueprint | None = None
        alignment: HiringManagerAlignment | None = None
        if job.project_id is not None:
            blueprint = await self._blueprints.get_by_project_id(job.project_id)
            alignment = await self._alignments.get_by_project_id(job.project_id)

        semaphore = asyncio.Semaphore(_COMPUTE_CONCURRENCY)

        async def _score_one(
            passport: Any,
        ) -> tuple[Any, dict[str, Any] | None, PassportMatchDraft | None]:
            # Same "only the LLM call runs concurrently" discipline as batch_get_or_compute_
            # matches -- the DB write happens afterward, one at a time, back on the main
            # coroutine (see _score_via_llm's docstring).
            version = await self._versions.get_by_id(passport.current_version_id)
            if version is None:
                return passport, None, None
            async with semaphore:
                try:
                    return (
                        passport,
                        version.snapshot,
                        await self._score_via_llm(
                            passport_snapshot=version.snapshot,
                            job=job,
                            blueprint=blueprint,
                            alignment=alignment,
                        ),
                    )
                except PassportMatchGenerationError:
                    # One candidate's score failing shouldn't blank out the whole search --
                    # same "fail open" discipline as the batch match endpoint.
                    return passport, None, None

        scored = await asyncio.gather(*(_score_one(p) for p in candidates))

        results: list[CandidateSearchResult] = []
        for passport, passport_snapshot, draft in scored:
            if draft is None or passport_snapshot is None:
                continue
            match = await self._persist_match(
                passport_version_id=passport.current_version_id,
                job=job,
                passport_snapshot=passport_snapshot,
                draft=draft,
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
                    dimension_breakdown=match.dimension_breakdown,
                    relationship_status=relationship_statuses.get(
                        passport.candidate_user_id, "new"
                    ),
                )
            )

        results.sort(key=lambda r: r.match_score, reverse=True)
        return results[:_MAX_SEARCH_RESULTS]

    async def search_talent_pool_for_job(
        self, *, actor: User, job_id: uuid.UUID
    ) -> list[TalentPoolMatchResult]:
        """Rank this company's granted Talent Pool candidates against a role -- the future
        Hiring Blueprint matching step of Talent Memory (talent_pool/__init__.py). Reuses every
        scoring/caching primitive search_candidates_for_job already established; the only real
        difference is where the candidate pool comes from (talent_pool_grants, scoped by the
        candidate's own chosen project_only/company_wide permission, instead of every
        discoverable Passport)."""
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.company_id != actor.company_id or job.deleted_at is not None:
            raise ShadowJobNotFoundError()

        grants = await self._talent_pool_grants.list_eligible_for_job(
            company_id=actor.company_id, project_id=job.project_id
        )
        if not grants:
            return []

        blueprint: HiringBlueprint | None = None
        alignment: HiringManagerAlignment | None = None
        if job.project_id is not None:
            blueprint = await self._blueprints.get_by_project_id(job.project_id)
            alignment = await self._alignments.get_by_project_id(job.project_id)

        semaphore = asyncio.Semaphore(_COMPUTE_CONCURRENCY)

        async def _score_one(
            grant: TalentPoolGrant,
        ) -> tuple[TalentPoolGrant, Any, dict[str, Any] | None, PassportMatchDraft | None]:
            passport = await self._passports.get_by_candidate_user_id(grant.candidate_user_id)
            if passport is None or passport.current_version_id is None:
                return grant, None, None, None
            version = await self._versions.get_by_id(passport.current_version_id)
            if version is None:
                return grant, None, None, None
            async with semaphore:
                try:
                    return (
                        grant,
                        passport,
                        version.snapshot,
                        await self._score_via_llm(
                            passport_snapshot=version.snapshot,
                            job=job,
                            blueprint=blueprint,
                            alignment=alignment,
                        ),
                    )
                except PassportMatchGenerationError:
                    # One candidate's score failing shouldn't blank the whole list -- same "fail
                    # open" discipline as search_candidates_for_job.
                    return grant, passport, None, None

        scored = await asyncio.gather(*(_score_one(g) for g in grants))

        company = await self._session.get(Company, job.company_id)
        job_url = f"{self._settings.frontend_base_url}/shadow/jobs/{job.id}"

        results: list[TalentPoolMatchResult] = []
        for grant, passport, passport_snapshot, draft in scored:
            if draft is None or passport is None or passport_snapshot is None:
                continue
            match = await self._persist_match(
                passport_version_id=passport.current_version_id,
                job=job,
                passport_snapshot=passport_snapshot,
                draft=draft,
            )
            await self._maybe_notify_candidate_of_match(match, company=company, job_url=job_url)
            career_entries = await self._career_entries.list_by_passport_id(passport.id)
            results.append(
                TalentPoolMatchResult(
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
                    dimension_breakdown=match.dimension_breakdown,
                    relationship_status="in_talent_pool",
                    source_role_title=grant.source_role_title,
                    scope=TalentPoolScope(grant.scope),
                    granted_at=grant.responded_at or grant.created_at,
                )
            )

        results.sort(key=lambda r: r.match_score, reverse=True)
        return results[:_MAX_SEARCH_RESULTS]

    async def _maybe_notify_candidate_of_match(
        self, match: PassportJobMatch, *, company: Company | None, job_url: str
    ) -> None:
        """Emails the candidate once per (passport_version, shadow_job) match -- never twice, and
        never for a Weak Match (still visible everywhere in-app, just not worth an inbox
        interruption). Mirrors JobAlertService.notify_matching_alerts's exact discipline: a send
        failure must never fail the recruiter's search request it's riding along with."""
        if (
            self._email_sender is None
            or match.candidate_notified_at is not None
            or match.match_tier not in _NOTIFY_MIN_TIER
            or company is None
        ):
            return

        passport_version = await self._versions.get_by_id(match.passport_version_id)
        if passport_version is None:
            return
        passport = await self._passports.get_by_id(passport_version.passport_id)
        if passport is None:
            return
        candidate = await self._candidate_users.get_by_id(passport.candidate_user_id)
        if candidate is None:
            return

        subject, body = build_talent_pool_match_email(company_name=company.name, job_url=job_url)
        try:
            await self._email_sender.send(to=candidate.email, subject=subject, body=body)
        except Exception:
            logger.exception(
                "Failed to send Talent Pool match email to candidate %s for match %s",
                candidate.id,
                match.id,
            )
            return
        await self._matches.mark_candidate_notified(match.id)

    async def list_talent_pool_opportunities(
        self, *, candidate: CandidateUser
    ) -> list[TalentPoolOpportunity]:
        """The candidate's own view of real matches companies have computed against their Talent
        Pool grants -- the other half of the opportunity workflow: search_talent_pool_for_job
        computes and (optionally) emails about a match, this is what the candidate actually sees
        when they follow up in the app."""
        passport_version_id = await self._resolve_approved_passport_version_id(candidate)
        company_ids = await self._talent_pool_grants.list_granted_company_ids_by_candidate(
            candidate.id
        )
        if not company_ids:
            return []

        matches = await self._matches.list_by_candidate_version_and_companies(
            passport_version_id=passport_version_id, company_ids=company_ids
        )

        opportunities: list[TalentPoolOpportunity] = []
        for match in matches:
            job = await self._jobs.get_by_id(match.shadow_job_id)
            if job is None or job.deleted_at is not None:
                continue
            if job.status != ShadowJobStatus.PUBLISHED.value:
                continue
            existing_application = await self._applications.get_by_job_and_candidate(
                shadow_job_id=job.id, candidate_user_id=candidate.id
            )
            if existing_application is not None:
                # Already tracked on the candidate's own Applications page -- showing it again
                # here as a fresh "opportunity" would just be a confusing duplicate.
                continue
            company = await self._session.get(Company, job.company_id)
            opportunities.append(
                TalentPoolOpportunity(
                    job_id=job.id,
                    job_title=job.title,
                    company_name=company.name if company else "Unknown company",
                    match_tier=match.match_tier,  # type: ignore[arg-type]
                    match_score=match.match_score,
                    match_summary=match.summary,
                    strengths=match.strengths,
                    gaps=match.gaps,
                    dimension_breakdown=match.dimension_breakdown,
                    generated_at=match.generated_at,
                )
            )

        opportunities.sort(key=lambda o: o.match_score, reverse=True)
        return opportunities

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
            dimension_breakdown=match.dimension_breakdown,
            generated_at=match.generated_at,
        )
