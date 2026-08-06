import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.candidates.models import Candidate, CandidateStatus
from app.modules.candidates.repository import CandidateRepository
from app.modules.dashboard.schemas import ActionItem, DashboardStats
from app.modules.hiring_manager_alignment.repository import HiringManagerAlignmentRepository
from app.modules.prescreen_assessment.repository import PrescreenAssessmentRepository
from app.modules.projects.models import Project, ProjectStatus
from app.modules.projects.repository import ProjectRepository

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

    async def get_dashboard_stats(self, *, company_id: uuid.UUID) -> DashboardStats:
        projects = await self._projects.list_by_company(company_id, limit=_MAX_ROWS)
        candidates = await self._candidates.list_by_company(company_id, limit=_MAX_ROWS)
        project_by_id = {p.id: p for p in projects}

        prescreen_stage = [c for c in candidates if c.status == _PRESCREEN_STATUS]
        hiring_manager_stage = [c for c in candidates if c.status == _HIRING_MANAGER_STATUS]

        assessments = await self._assessments.list_by_candidate_ids([c.id for c in candidates])
        assessed_candidate_ids = {a.candidate_id for a in assessments}
        aligned_project_ids = await self._alignments.list_project_ids_by_company(company_id)

        action_items = self._build_action_items(
            projects=projects,
            project_by_id=project_by_id,
            prescreen_stage=prescreen_stage,
            hiring_manager_stage=hiring_manager_stage,
            assessed_candidate_ids=assessed_candidate_ids,
            aligned_project_ids=aligned_project_ids,
        )

        return DashboardStats(
            live_projects=sum(1 for p in projects if p.status in _LIVE_PROJECT_STATUSES),
            candidates_in_process=sum(1 for c in candidates if c.status in _IN_PROCESS_STATUSES),
            prescreen_stage_count=len(prescreen_stage),
            hiring_manager_stage_count=len(hiring_manager_stage),
            action_item_count=len(action_items),
            action_items=action_items[:_MAX_ACTION_ITEMS],
        )

    def _build_action_items(
        self,
        *,
        projects: list[Project],
        project_by_id: dict[uuid.UUID, Project],
        prescreen_stage: list[Candidate],
        hiring_manager_stage: list[Candidate],
        assessed_candidate_ids: set[uuid.UUID],
        aligned_project_ids: set[uuid.UUID],
    ) -> list[ActionItem]:
        items: list[ActionItem] = []

        # Highest priority — an AI recommendation is sitting unactioned.
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
