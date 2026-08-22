import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.candidates.models import Candidate, CandidateStatus
from app.modules.candidates.repository import CandidateRepository
from app.modules.dashboard.schemas import ActionItem, DashboardStats
from app.modules.hiring_manager_alignment.repository import HiringManagerAlignmentRepository
from app.modules.interviews.repository import InterviewRepository
from app.modules.prescreen_assessment.repository import PrescreenAssessmentRepository
from app.modules.projects.models import Project, ProjectStatus
from app.modules.projects.repository import ProjectRepository
from app.modules.shadow_jobs.models import (
    ShadowApplication,
    ShadowApplicationStatus,
    ShadowJob,
    ShadowPipelineStage,
)
from app.modules.shadow_jobs.repository import ShadowApplicationRepository, ShadowJobRepository
from app.modules.shadow_reveal.models import RevealRequestStatus, ShadowRevealRequest
from app.modules.shadow_reveal.repository import ShadowRevealRequestRepository

# A company's live pipeline is at most a few hundred projects/candidates in practice — same
# unpaginated-read reasoning as analytics.service._MAX_CANDIDATES.
_MAX_ROWS = 5000

# "Live" = still an active hiring effort. filled/cancelled are terminal — excluded so the count
# reflects roles a recruiter actually needs to keep working, not the full historical list.
_LIVE_PROJECT_STATUSES = {
    ProjectStatus.DRAFT.value,
    ProjectStatus.OPEN.value,
    ProjectStatus.ON_HOLD.value,
}

# Candidates still moving through the pipeline — excludes the three terminal statuses.
_IN_PROCESS_STATUSES = {
    CandidateStatus.NEW.value,
    CandidateStatus.SCREENING.value,
    CandidateStatus.INTERVIEWING.value,
    CandidateStatus.OFFER.value,
}

# The kanban's "Screening" column is the pre-screen stage; "Interviewing" is where the candidate
# has been handed off to the hiring manager. There's no separate status for these two concepts —
# they map directly onto CandidateStatus.
_PRESCREEN_STATUS = CandidateStatus.SCREENING.value
_HIRING_MANAGER_STATUS = CandidateStatus.INTERVIEWING.value

# Caps the list surfaced to the UI so the panel stays scannable — action_item_count on the
# response still reflects the true total even when the list itself is truncated.
_MAX_ACTION_ITEMS = 20


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._projects = ProjectRepository(session)
        self._candidates = CandidateRepository(session)
        self._assessments = PrescreenAssessmentRepository(session)
        self._alignments = HiringManagerAlignmentRepository(session)
        self._shadow_applications = ShadowApplicationRepository(session)
        self._shadow_jobs = ShadowJobRepository(session)
        self._reveal_requests = ShadowRevealRequestRepository(session)
        self._interviews = InterviewRepository(session)

    async def get_dashboard_stats(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID | None = None
    ) -> DashboardStats:
        projects = await self._projects.list_by_company(company_id, limit=_MAX_ROWS)
        candidates = await self._candidates.list_by_company(company_id, limit=_MAX_ROWS)
        if project_id is not None:
            # Scoped call (e.g. a role's own Role Health view) -- every count below becomes
            # this-project-only, and the _MAX_ACTION_ITEMS cap (sized for the company-wide
            # panel's own readability) doesn't apply: a single project's real gap count is
            # always small, and truncating it here would let Role Health silently under-report.
            projects = [p for p in projects if p.id == project_id]
            candidates = [c for c in candidates if c.project_id == project_id]
        project_by_id = {p.id: p for p in projects}

        prescreen_stage = [c for c in candidates if c.status == _PRESCREEN_STATUS]
        hiring_manager_stage = [c for c in candidates if c.status == _HIRING_MANAGER_STATUS]

        assessments = await self._assessments.list_by_candidate_ids([c.id for c in candidates])
        assessed_candidate_ids = {a.candidate_id for a in assessments}
        aligned_project_ids = await self._alignments.list_project_ids_by_company(company_id)

        unseen_reveals = await self._resolve_unseen_reveal_responses(
            company_id=company_id, project_id=project_id
        )
        needs_interview_arranged = await self._resolve_needs_interview_arranged(
            company_id=company_id, project_id=project_id
        )

        action_items = self._build_action_items(
            projects=projects,
            project_by_id=project_by_id,
            prescreen_stage=prescreen_stage,
            hiring_manager_stage=hiring_manager_stage,
            assessed_candidate_ids=assessed_candidate_ids,
            aligned_project_ids=aligned_project_ids,
            unseen_reveals=unseen_reveals,
            needs_interview_arranged=needs_interview_arranged,
        )

        max_items = len(action_items) if project_id is not None else _MAX_ACTION_ITEMS
        return DashboardStats(
            live_projects=sum(1 for p in projects if p.status in _LIVE_PROJECT_STATUSES),
            candidates_in_process=sum(1 for c in candidates if c.status in _IN_PROCESS_STATUSES),
            prescreen_stage_count=len(prescreen_stage),
            hiring_manager_stage_count=len(hiring_manager_stage),
            action_item_count=len(action_items),
            action_items=action_items[:max_items],
        )

    async def _resolve_unseen_reveal_responses(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID | None
    ) -> list[tuple[ShadowRevealRequest, ShadowApplication, ShadowJob]]:
        """Every reveal response nobody's opened the applicant's card for since, resolved down
        to (request, application, job) triples so _build_action_items has everything it needs
        without its own lookups. Scoped to project_id when given, same as every other stat here."""
        requests = await self._reveal_requests.list_unseen_responses_by_company(company_id)
        resolved: list[tuple[ShadowRevealRequest, ShadowApplication, ShadowJob]] = []
        for request in requests:
            application = await self._shadow_applications.get_by_id(request.shadow_application_id)
            if application is None:
                continue
            job = await self._shadow_jobs.get_by_id(application.shadow_job_id)
            if job is None:
                continue
            if project_id is not None and job.project_id != project_id:
                continue
            resolved.append((request, application, job))
        return resolved

    async def _resolve_needs_interview_arranged(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID | None
    ) -> list[tuple[ShadowApplication, ShadowJob]]:
        """Applicants who revealed their identity (which only ever happens after the company
        requested it -- "expressed interest") but have no interview arranged yet. Rejected
        applicants are excluded -- a recruiter who's already passed on someone doesn't need to be
        told to interview them. Any interview record at all (not just an upcoming one) counts as
        "arranged", so this clears the moment one is scheduled even if it's later completed."""
        applications = await self._shadow_applications.list_by_company_id(company_id)
        revealed = [
            a
            for a in applications
            if a.status == ShadowApplicationStatus.REVEALED.value
            and a.pipeline_stage != ShadowPipelineStage.REJECTED.value
        ]
        if not revealed:
            return []
        arranged_ids = {
            i.shadow_application_id
            for i in await self._interviews.list_by_application_ids([a.id for a in revealed])
        }
        resolved: list[tuple[ShadowApplication, ShadowJob]] = []
        for application in revealed:
            if application.id in arranged_ids:
                continue
            job = await self._shadow_jobs.get_by_id(application.shadow_job_id)
            if job is None:
                continue
            if project_id is not None and job.project_id != project_id:
                continue
            resolved.append((application, job))
        return resolved

    def _build_action_items(
        self,
        *,
        projects: list[Project],
        project_by_id: dict[uuid.UUID, Project],
        prescreen_stage: list[Candidate],
        hiring_manager_stage: list[Candidate],
        assessed_candidate_ids: set[uuid.UUID],
        aligned_project_ids: set[uuid.UUID],
        unseen_reveals: list[tuple[ShadowRevealRequest, ShadowApplication, ShadowJob]],
        needs_interview_arranged: list[tuple[ShadowApplication, ShadowJob]],
    ) -> list[ActionItem]:
        items: list[ActionItem] = []

        # Highest priority — a candidate is waiting on the other end of this decision.
        for request, application, job in unseen_reveals:
            verb = (
                "approved" if request.status == RevealRequestStatus.APPROVED.value else "declined"
            )
            items.append(
                ActionItem(
                    type="reveal_response_needs_review",
                    message=f"{application.callsign} {verb} your reveal request for {job.title}",
                    project_id=job.project_id,
                    project_title=job.title,
                    candidate_id=None,
                    candidate_callsign=application.callsign,
                    shadow_job_id=job.id,
                    application_id=application.id,
                )
            )

        # Next priority — identity's revealed, the ball's in our court to set up time.
        for application, job in needs_interview_arranged:
            items.append(
                ActionItem(
                    type="needs_interview_arranged",
                    message=(
                        f"{application.callsign} revealed their identity — "
                        f"arrange an interview for {job.title}"
                    ),
                    project_id=job.project_id,
                    project_title=job.title,
                    candidate_id=None,
                    candidate_callsign=application.callsign,
                    shadow_job_id=job.id,
                    application_id=application.id,
                )
            )

        # Next priority — an AI recommendation is sitting unactioned.
        for c in prescreen_stage:
            if c.id in assessed_candidate_ids and c.prescreen_outcome == "advance":
                project = project_by_id.get(c.project_id)
                if project is None:
                    continue
                items.append(
                    ActionItem(
                        type="ready_to_advance",
                        message=f"{c.callsign} was recommended to advance — move to Interviewing",
                        project_id=project.id,
                        project_title=project.title,
                        candidate_id=c.id,
                        candidate_callsign=c.callsign,
                    )
                )

        for c in hiring_manager_stage:
            if c.interview_scheduled_at is None:
                project = project_by_id.get(c.project_id)
                if project is None:
                    continue
                items.append(
                    ActionItem(
                        type="needs_interview_scheduling",
                        message=f"{c.callsign} has no interview scheduled yet",
                        project_id=project.id,
                        project_title=project.title,
                        candidate_id=c.id,
                        candidate_callsign=c.callsign,
                    )
                )

        for c in prescreen_stage:
            if c.id not in assessed_candidate_ids:
                project = project_by_id.get(c.project_id)
                if project is None:
                    continue
                items.append(
                    ActionItem(
                        type="needs_prescreen",
                        message=f"{c.callsign} is awaiting a pre-screen assessment",
                        project_id=project.id,
                        project_title=project.title,
                        candidate_id=c.id,
                        candidate_callsign=c.callsign,
                    )
                )

        for p in projects:
            if p.status in _LIVE_PROJECT_STATUSES and p.id not in aligned_project_ids:
                items.append(
                    ActionItem(
                        type="needs_alignment",
                        message=f"{p.title} has no hiring manager alignment submitted",
                        project_id=p.id,
                        project_title=p.title,
                        candidate_id=None,
                        candidate_callsign=None,
                    )
                )

        return items
