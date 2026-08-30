import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.candidate_activity.diffing import diff_passport_snapshots
from app.modules.candidate_activity.schemas import (
    AiRecommendation,
    RediscoveryCandidate,
    TimelineEntry,
)
from app.modules.messages.repository import MessageThreadRepository
from app.modules.passport_matching.exceptions import ShadowJobNotFoundError
from app.modules.passport_matching.llm_client import PassportMatchingLLMClient
from app.modules.passport_matching.models import CandidatePass
from app.modules.passport_matching.repository import CandidatePassRepository
from app.modules.passport_matching.service import PassportMatchingService
from app.modules.phantom_passport.models import PhantomPassport
from app.modules.phantom_passport.repository import (
    PassportVersionRepository,
    PhantomPassportRepository,
)
from app.modules.shadow_introduction.models import IntroductionRequest
from app.modules.shadow_introduction.repository import IntroductionRequestRepository
from app.modules.shadow_jobs.models import ShadowApplication, ShadowJobStatus
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository
from app.modules.shadow_reveal.models import ShadowRevealRequest
from app.modules.shadow_reveal.repository import ShadowRevealRequestRepository
from app.modules.talent_pool.models import TalentPoolGrant
from app.modules.talent_pool.repository import TalentPoolGrantRepository

CallsignByCandidate = dict[uuid.UUID, str]
CallsignByRevealId = dict[uuid.UUID, str | None]


def _is_discoverable(passport: PhantomPassport) -> bool:
    """Same eligibility gate used everywhere else in this codebase (talent_pool.service,
    shadow_introduction.service) -- re-checked here too since a rediscovery candidate may have
    gone private or "not looking" since being passed on."""
    return (
        passport.visibility != "private"
        and passport.career_intent != "not_looking"
        and passport.current_version_id is not None
        and passport.deleted_at is None
    )


class CandidateActivityService:
    def __init__(
        self, session: AsyncSession, *, llm_client: PassportMatchingLLMClient | None = None
    ) -> None:
        self._session = session
        self._applications = ShadowApplicationRepository(session)
        self._reveals = ShadowRevealRequestRepository(session)
        self._grants = TalentPoolGrantRepository(session)
        self._passes = CandidatePassRepository(session)
        self._introductions = IntroductionRequestRepository(session)
        self._threads = MessageThreadRepository(session)
        self._passports = PhantomPassportRepository(session)
        self._versions = PassportVersionRepository(session)
        self._jobs = ShadowJobRepository(session)
        self._llm_client = llm_client

    # --- Interaction timeline ----------------------------------------------------------------

    async def list_candidate_timeline(self, *, actor: User, callsign: str) -> list[TimelineEntry]:
        passport = await self._passports.get_by_callsign(callsign)
        if passport is None:
            raise ShadowJobNotFoundError()

        candidate_user_id = passport.candidate_user_id
        company_id = actor.company_id

        applications = [
            a
            for a in await self._applications.list_by_company_id(company_id)
            if a.candidate_user_id == candidate_user_id
        ]
        reveals = await self._reveals.list_by_company_and_candidate(
            company_id=company_id, candidate_user_id=candidate_user_id
        )
        grants = await self._grants.list_by_company_and_candidate(
            company_id=company_id, candidate_user_id=candidate_user_id
        )
        passes = [
            p
            for p in await self._passes.list_by_company_id(company_id)
            if p.candidate_user_id == candidate_user_id
        ]
        introductions = await self._introductions.list_by_company_and_candidate(
            company_id=company_id, candidate_user_id=candidate_user_id
        )
        threads = await self._threads.list_by_company_and_candidate(
            company_id=company_id, candidate_user_id=candidate_user_id
        )

        entries: list[TimelineEntry] = []
        entries.extend(_application_entries(applications))
        entries.extend(_reveal_entries(reveals))
        entries.extend(_grant_entries(grants))
        entries.extend(_pass_entries(passes))
        entries.extend(_introduction_entries(introductions))
        for thread in threads:
            entries.append(
                TimelineEntry(
                    event_type="conversation_started",
                    description="Conversation started",
                    occurred_at=thread.created_at,
                )
            )

        entries.sort(key=lambda e: e.occurred_at, reverse=True)
        return entries

    async def list_recent_company_activity(
        self, *, actor: User, limit: int = 15
    ) -> list[TimelineEntry]:
        company_id = actor.company_id

        applications = await self._applications.list_by_company_id(company_id)
        reveals = await self._reveals.list_by_company_id(company_id)
        grants = await self._grants.list_by_company_id(company_id)
        passes = await self._passes.list_by_company_id(company_id)
        introductions = await self._introductions.list_by_company_id(company_id)
        threads = await self._threads.list_by_company_id(company_id)

        # One batch lookup for every candidate_user_id involved -- avoids an N+1 passport fetch
        # per event, mirrors _compute_relationship_statuses's own "resolve once, merge in
        # Python" style.
        candidate_ids: set[uuid.UUID] = set()
        candidate_ids.update(a.candidate_user_id for a in applications)
        candidate_ids.update(g.candidate_user_id for g in grants)
        candidate_ids.update(p.candidate_user_id for p in passes)
        candidate_ids.update(i.candidate_user_id for i in introductions)
        candidate_ids.update(t.candidate_user_id for t in threads)

        application_by_id = {a.id: a for a in applications}
        for reveal in reveals:
            application = application_by_id.get(reveal.shadow_application_id)
            if application is not None:
                candidate_ids.add(application.candidate_user_id)

        callsign_by_candidate: dict[uuid.UUID, str] = {}
        for candidate_id in candidate_ids:
            passport = await self._passports.get_by_candidate_user_id(candidate_id)
            if passport is not None and passport.callsign is not None:
                callsign_by_candidate[candidate_id] = passport.callsign

        entries: list[TimelineEntry] = []
        entries.extend(_application_entries(applications, callsign_by_candidate))
        entries.extend(
            _reveal_entries(
                reveals,
                callsign_by_candidate={
                    reveal.id: callsign_by_candidate.get(
                        application_by_id[reveal.shadow_application_id].candidate_user_id
                    )
                    for reveal in reveals
                    if reveal.shadow_application_id in application_by_id
                },
            )
        )
        entries.extend(_grant_entries(grants, callsign_by_candidate))
        entries.extend(_pass_entries(passes, callsign_by_candidate))
        entries.extend(_introduction_entries(introductions, callsign_by_candidate))
        for thread in threads:
            callsign = callsign_by_candidate.get(thread.candidate_user_id)
            entries.append(
                TimelineEntry(
                    event_type="conversation_started",
                    description=f"Conversation started with {callsign or 'a candidate'}",
                    occurred_at=thread.created_at,
                    callsign=callsign,
                )
            )

        entries.sort(key=lambda e: e.occurred_at, reverse=True)
        return entries[:limit]

    # --- Candidate Rediscovery -----------------------------------------------------------------

    async def list_rediscovery_candidates(self, *, actor: User) -> list[RediscoveryCandidate]:
        passes = await self._passes.list_by_company_id(actor.company_id)
        results: list[RediscoveryCandidate] = []

        for pass_row in passes:
            passport = await self._passports.get_by_candidate_user_id(pass_row.candidate_user_id)
            if passport is None or not _is_discoverable(passport):
                continue
            if passport.current_version_id is None:
                continue

            versions = await self._versions.list_by_passport_id(passport.id)
            versions_before_pass = [v for v in versions if v.approved_at <= pass_row.created_at]
            if not versions_before_pass:
                continue
            old_version = versions_before_pass[0]
            if old_version.id == passport.current_version_id:
                continue

            current_version = await self._versions.get_by_id(passport.current_version_id)
            if current_version is None:
                continue

            changes = diff_passport_snapshots(old_version.snapshot, current_version.snapshot)
            if not changes:
                continue

            job_title: str | None = None
            if pass_row.shadow_job_id is not None:
                job = await self._jobs.get_by_id(pass_row.shadow_job_id)
                job_title = job.title if job is not None else None

            results.append(
                RediscoveryCandidate(
                    callsign=passport.callsign or "Unknown",
                    headline=passport.headline,
                    seniority=passport.seniority,
                    changes=changes,
                    passed_reason=pass_row.reason,  # type: ignore[arg-type]
                    passed_shadow_job_id=pass_row.shadow_job_id,
                    passed_for_job_title=job_title,
                    passed_at=pass_row.created_at,
                )
            )

        results.sort(key=lambda r: r.passed_at, reverse=True)
        return results

    # --- AI Recommendation ---------------------------------------------------------------------

    async def get_ai_recommendation(self, *, actor: User) -> AiRecommendation | None:
        if self._llm_client is None:
            return None

        jobs = await self._jobs.list_by_company(actor.company_id, limit=200)
        published = [j for j in jobs if j.status == ShadowJobStatus.PUBLISHED.value]
        if not published:
            return None
        published.sort(key=lambda j: j.published_at or j.created_at, reverse=True)
        job = published[0]

        results = await PassportMatchingService(
            self._session, llm_client=self._llm_client
        ).search_candidates_for_job(actor=actor, job_id=job.id)
        candidate = next((r for r in results if r.relationship_status == "new"), None)
        if candidate is None:
            return None

        return AiRecommendation(
            job_id=job.id,
            job_title=job.title,
            callsign=candidate.callsign,
            match_tier=candidate.match_tier,
            match_score=candidate.match_score,
            match_summary=candidate.match_summary,
        )


def _application_entries(
    applications: list[ShadowApplication],
    callsign_by_candidate: CallsignByCandidate | None = None,
) -> list[TimelineEntry]:
    entries = []
    for app in applications:
        callsign = callsign_by_candidate.get(app.candidate_user_id) if callsign_by_candidate else None
        entries.append(
            TimelineEntry(
                event_type="application_submitted",
                description=(
                    f"{callsign} applied" if callsign else "Applied to a role"
                ),
                occurred_at=app.created_at,
                callsign=callsign,
            )
        )
    return entries


def _reveal_entries(
    reveals: list[ShadowRevealRequest],
    callsign_by_candidate: CallsignByRevealId | None = None,
) -> list[TimelineEntry]:
    entries = []
    for reveal in reveals:
        callsign = callsign_by_candidate.get(reveal.id) if callsign_by_candidate else None
        prefix = f"{callsign}: " if callsign else ""
        entries.append(
            TimelineEntry(
                event_type="reveal_requested",
                description=f"{prefix}Identity reveal requested",
                occurred_at=reveal.created_at,
                callsign=callsign,
            )
        )
        if reveal.responded_at is not None:
            outcome = "approved" if reveal.status == "approved" else "declined"
            entries.append(
                TimelineEntry(
                    event_type="reveal_responded",
                    description=f"{prefix}Identity reveal {outcome}",
                    occurred_at=reveal.responded_at,
                    callsign=callsign,
                )
            )
    return entries


def _grant_entries(
    grants: list[TalentPoolGrant], callsign_by_candidate: CallsignByCandidate | None = None
) -> list[TimelineEntry]:
    entries = []
    for grant in grants:
        callsign = callsign_by_candidate.get(grant.candidate_user_id) if callsign_by_candidate else None
        prefix = f"{callsign}: " if callsign else ""
        entries.append(
            TimelineEntry(
                event_type="talent_pool_requested",
                description=f"{prefix}Asked to be kept on file for {grant.source_role_title}",
                occurred_at=grant.created_at,
                callsign=callsign,
            )
        )
        if grant.responded_at is not None:
            outcome = "granted" if grant.status == "granted" else "declined"
            entries.append(
                TimelineEntry(
                    event_type="talent_pool_responded",
                    description=f"{prefix}Talent Pool request {outcome}",
                    occurred_at=grant.responded_at,
                    callsign=callsign,
                )
            )
        if grant.withdrawn_at is not None:
            entries.append(
                TimelineEntry(
                    event_type="talent_pool_withdrawn",
                    description=f"{prefix}Withdrew from Talent Pool",
                    occurred_at=grant.withdrawn_at,
                    callsign=callsign,
                )
            )
    return entries


def _pass_entries(
    passes: list[CandidatePass], callsign_by_candidate: CallsignByCandidate | None = None
) -> list[TimelineEntry]:
    entries = []
    for pass_row in passes:
        callsign = (
            callsign_by_candidate.get(pass_row.candidate_user_id) if callsign_by_candidate else None
        )
        prefix = f"{callsign}: " if callsign else ""
        reason_suffix = f" ({pass_row.reason})" if pass_row.reason else ""
        entries.append(
            TimelineEntry(
                event_type="passed",
                description=f"{prefix}Passed{reason_suffix}",
                occurred_at=pass_row.created_at,
                callsign=callsign,
            )
        )
    return entries


def _introduction_entries(
    introductions: list[IntroductionRequest],
    callsign_by_candidate: CallsignByCandidate | None = None,
) -> list[TimelineEntry]:
    entries = []
    for intro in introductions:
        callsign = (
            callsign_by_candidate.get(intro.candidate_user_id) if callsign_by_candidate else None
        )
        prefix = f"{callsign}: " if callsign else ""
        entries.append(
            TimelineEntry(
                event_type="introduction_requested",
                description=f"{prefix}Requested an introduction",
                occurred_at=intro.created_at,
                callsign=callsign,
            )
        )
        if intro.responded_at is not None:
            outcome = "accepted" if intro.status == "accepted" else "declined"
            entries.append(
                TimelineEntry(
                    event_type="introduction_responded",
                    description=f"{prefix}Introduction {outcome}",
                    occurred_at=intro.responded_at,
                    callsign=callsign,
                )
            )
    return entries
