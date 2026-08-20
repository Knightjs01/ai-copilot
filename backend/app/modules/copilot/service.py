import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.candidate_auth.models import CandidateUser
from app.modules.copilot.exceptions import CopilotGenerationError
from app.modules.copilot.llm_client import CopilotLLMClient, LLMRequestError
from app.modules.copilot.schemas import CopilotChatRequest, CopilotChatResponse
from app.modules.interviews.service import InterviewService
from app.modules.passport_matching.exceptions import (
    PassportNotApprovedError,
    ShadowJobNotFoundError,
)
from app.modules.passport_matching.llm_client import PassportMatchingLLMClient
from app.modules.passport_matching.schemas import BoardFilters
from app.modules.passport_matching.service import PassportMatchingService
from app.modules.phantom_passport.llm_client import LLMClient as PhantomPassportLLMClient
from app.modules.phantom_passport.repository import PhantomPassportRepository
from app.modules.phantom_passport.service import PhantomPassportService
from app.modules.shadow_jobs.exceptions import ShadowApplicationNotFoundError
from app.modules.shadow_jobs.models import ShadowJob
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository
from app.modules.shadow_jobs.service import ShadowJobService

_DEFAULT_REPLY = (
    "I can help you search jobs, explain a match, improve your Passport, check your "
    "application status, or prep for an interview — what would you like?"
)


def _job_facts(job: ShadowJob) -> dict[str, object]:
    # Duplicated from passport_matching/service.py's own _job_facts rather than imported —
    # small, cross-module helper duplication is this codebase's established convention (see
    # shadow_jobs/service.py's own duplicated unread-count bulk lookup) over reaching into
    # another module's private internals.
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


def _format_search_reply(filters: BoardFilters) -> str:
    parts: list[str] = []
    if filters.seniority:
        parts.append(f"seniority: {filters.seniority}")
    if filters.remote_preference:
        parts.append(f"remote preference: {filters.remote_preference}")
    if filters.employment_type:
        parts.append(f"employment type: {filters.employment_type}")
    if filters.location:
        parts.append(f"location: {filters.location}")
    if not parts:
        return (
            "I couldn't pin down specific filters from that — try browsing Discover directly, "
            "or be more specific (e.g. remote, seniority, location)."
        )
    return (
        "Here's what I understood: "
        + ", ".join(parts)
        + ". Head to Discover to see matching roles."
    )


class CopilotService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        copilot_llm_client: CopilotLLMClient,
        passport_matching_llm_client: PassportMatchingLLMClient,
        phantom_passport_llm_client: PhantomPassportLLMClient,
    ) -> None:
        self._session = session
        self._llm_client = copilot_llm_client
        self._matching = PassportMatchingService(session, llm_client=passport_matching_llm_client)
        self._passport_service = PhantomPassportService(
            session, llm_client=phantom_passport_llm_client
        )
        self._passports = PhantomPassportRepository(session)
        self._shadow_jobs = ShadowJobService(session)
        self._interviews = InterviewService(session)
        self._applications = ShadowApplicationRepository(session)
        self._jobs = ShadowJobRepository(session)

    async def chat(
        self, *, candidate: CandidateUser, body: CopilotChatRequest
    ) -> CopilotChatResponse:
        history = [{"role": m.role, "content": m.content} for m in body.history]
        try:
            decision = await self._llm_client.route(
                message=body.message, history=history, context_type=body.context_type
            )
        except LLMRequestError as exc:
            raise CopilotGenerationError(str(exc)) from exc

        if decision.action == "search_jobs":
            return await self._search_jobs(decision.query or body.message)
        if decision.action == "explain_match":
            return await self._explain_match(candidate=candidate, body=body)
        if decision.action == "suggest_improvements":
            return await self._suggest_improvements(candidate=candidate)
        if decision.action == "summarize_applications":
            return await self._summarize_applications(candidate=candidate, body=body)
        if decision.action == "interview_prep":
            return await self._interview_prep(candidate=candidate, body=body)
        return CopilotChatResponse(reply=decision.message or _DEFAULT_REPLY, action="reply")

    async def _search_jobs(self, query: str) -> CopilotChatResponse:
        filters = await self._matching.parse_search_query(query=query)
        return CopilotChatResponse(
            reply=_format_search_reply(filters), action="search_jobs", board_filters=filters
        )

    async def _explain_match(
        self, *, candidate: CandidateUser, body: CopilotChatRequest
    ) -> CopilotChatResponse:
        if body.context_type != "job" or body.context_id is None:
            return CopilotChatResponse(
                reply="Open a specific job listing and ask me again — I'll explain how you match.",
                action="reply",
            )
        try:
            match = await self._matching.get_or_compute_match(
                candidate=candidate, shadow_job_id=body.context_id
            )
        except PassportNotApprovedError:
            return CopilotChatResponse(
                reply="Build and approve your Phantom Passport first, then I can explain your match.",
                action="reply",
            )
        except ShadowJobNotFoundError:
            return CopilotChatResponse(
                reply="I couldn't find that job listing — try opening it again.", action="reply"
            )
        reply = f"{match.match_tier} ({match.match_score}/100). {match.summary}"
        if match.strengths:
            reply += "\n\nStrengths: " + "; ".join(match.strengths)
        if match.gaps:
            reply += "\n\nAreas to note: " + "; ".join(match.gaps)
        return CopilotChatResponse(reply=reply, action="explain_match", match=match)

    async def _suggest_improvements(self, *, candidate: CandidateUser) -> CopilotChatResponse:
        passport = await self._passports.get_by_candidate_user_id(candidate.id)
        if passport is None:
            return CopilotChatResponse(
                reply="Build your Passport first, then I can suggest improvements.", action="reply"
            )
        suggestion = await self._passport_service.suggest_summary_improvement(
            headline=passport.headline, summary=passport.summary or "", skills=list(passport.skills)
        )
        reply = (
            "Here's a stronger version of your summary:\n\n"
            f"{suggestion.suggested_summary}\n\n"
            "Ask me to also suggest skills or industries."
        )
        return CopilotChatResponse(
            reply=reply,
            action="suggest_improvements",
            suggested_summary=suggestion.suggested_summary,
        )

    async def _summarize_applications(
        self, *, candidate: CandidateUser, body: CopilotChatRequest
    ) -> CopilotChatResponse:
        if body.context_type == "application" and body.context_id is not None:
            try:
                application = await self._shadow_jobs.get_my_application(
                    candidate=candidate, application_id=body.context_id
                )
            except ShadowApplicationNotFoundError:
                return CopilotChatResponse(
                    reply="I couldn't find that application — try opening it again.", action="reply"
                )
            applications = [application]
        else:
            applications = await self._shadow_jobs.list_my_applications(candidate=candidate)

        if not applications:
            return CopilotChatResponse(
                reply="You haven't applied to any roles yet — browse Discover to get started.",
                action="summarize_applications",
            )

        interviews = await self._interviews.list_for_candidate(candidate=candidate)
        interviews_by_application: dict[uuid.UUID, list[Any]] = defaultdict(list)
        for interview in interviews:
            interviews_by_application[interview.application_id].append(interview)

        lines: list[str] = []
        for application in applications:
            status_label = application.status.replace("_", " ").capitalize()
            line = f"• {application.job_title} at {application.company_name}: {status_label}"
            scheduled = [
                i
                for i in interviews_by_application.get(application.id, [])
                if i.status == "scheduled"
            ]
            if scheduled:
                next_interview = min(scheduled, key=lambda i: i.scheduled_at)
                line += f" — interview scheduled {next_interview.scheduled_at:%d %b %Y}"
            lines.append(line)

        intro = (
            "Here's your application:"
            if len(applications) == 1
            else f"You have {len(applications)} applications:"
        )
        return CopilotChatResponse(
            reply=intro + "\n\n" + "\n".join(lines), action="summarize_applications"
        )

    async def _interview_prep(
        self, *, candidate: CandidateUser, body: CopilotChatRequest
    ) -> CopilotChatResponse:
        if body.context_type != "interview" or body.context_id is None:
            return CopilotChatResponse(
                reply="Open a specific interview from your Interviews page and ask me again.",
                action="reply",
            )
        # Ownership check happens inside get_for_candidate -- a cross-candidate interview_id
        # raises InterviewNotFoundError (a real 404), not swallowed into a nudge here.
        interview = await self._interviews.get_for_candidate(
            candidate=candidate, interview_id=body.context_id
        )
        application = await self._applications.get_by_id(interview.application_id)
        job = await self._jobs.get_by_id(application.shadow_job_id) if application else None
        if application is None or job is None:
            return CopilotChatResponse(
                reply="I couldn't find the role for that interview.", action="reply"
            )
        try:
            questions = await self._llm_client.generate_interview_prep(job_facts=_job_facts(job))
        except LLMRequestError as exc:
            raise CopilotGenerationError(str(exc)) from exc
        reply = "Here are some questions to help you prepare:\n\n" + "\n".join(
            f"• {q}" for q in questions
        )
        return CopilotChatResponse(
            reply=reply, action="interview_prep", interview_prep_questions=questions
        )
