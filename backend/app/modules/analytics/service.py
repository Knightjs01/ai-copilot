import uuid
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.schemas import ProjectAnalytics, SalaryStats
from app.modules.candidates.service import CandidateService
from app.modules.prescreen_assessment.repository import PrescreenAssessmentRepository
from app.modules.projects.service import ProjectService

# Analytics reads every candidate under a project unpaginated — a hiring project's pool is at
# most a few hundred candidates in practice, nowhere near needing real pagination here.
_MAX_CANDIDATES = 5000


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._projects = ProjectService(session)
        self._candidates = CandidateService(session)
        self._assessments = PrescreenAssessmentRepository(session)

    async def get_project_analytics(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID
    ) -> ProjectAnalytics:
        # Confirms project_id belongs to company_id — raises ProjectNotFoundError (404)
        # otherwise, same pattern every other module uses when reaching across into projects.
        await self._projects.get_project(company_id=company_id, project_id=project_id)

        candidates = await self._candidates.list_candidates(
            company_id=company_id, project_id=project_id, limit=_MAX_CANDIDATES
        )
        assessments = await self._assessments.list_by_candidate_ids([c.id for c in candidates])

        salaries = [c.expected_salary for c in candidates if c.expected_salary is not None]

        return ProjectAnalytics(
            total_candidates=len(candidates),
            status_breakdown=dict(Counter(c.status for c in candidates)),
            prescreen_outcome_breakdown=dict(
                Counter(c.prescreen_outcome for c in candidates if c.prescreen_outcome)
            ),
            fit_rating_breakdown=dict(Counter(a.fit_rating for a in assessments)),
            source_breakdown=dict(Counter(c.source for c in candidates)),
            agency_breakdown=dict(
                Counter(c.agency_name for c in candidates if c.source == "agency" and c.agency_name)
            ),
            salary_stats=SalaryStats(
                count=len(salaries),
                average=round(sum(salaries) / len(salaries), 2) if salaries else None,
                minimum=min(salaries) if salaries else None,
                maximum=max(salaries) if salaries else None,
            ),
            location_breakdown=dict(Counter(c.location for c in candidates if c.location)),
            notice_period_breakdown=dict(
                Counter(c.notice_period for c in candidates if c.notice_period)
            ),
            current_employer_breakdown=dict(
                Counter(c.current_employer for c in candidates if c.current_employer)
            ),
        )
