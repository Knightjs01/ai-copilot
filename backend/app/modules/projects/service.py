import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.auth.service.user_service import UserService
from app.modules.commercial.service import CommercialService
from app.modules.hiring_blueprint.models import HiringBlueprint
from app.modules.hiring_blueprint.repository import HiringBlueprintRepository
from app.modules.hiring_manager_alignment.models import HiringManagerAlignment
from app.modules.hiring_manager_alignment.repository import HiringManagerAlignmentRepository
from app.modules.privacy_gateway.exceptions import ExtractionFailedError, UnsupportedFileTypeError
from app.modules.privacy_gateway.extraction import extract_text
from app.modules.projects.exceptions import (
    ActiveRoleLimitExceededError,
    InvalidHiringManagerError,
    InvalidProjectMemberError,
    JDExtractionFailedError,
    ProjectNotFoundError,
    ProjectNotReadyToApproveError,
    RoleFieldsExtractionFailedError,
    UnsupportedJDFileTypeError,
)
from app.modules.projects.llm_client import LLMRequestError, ProjectsLLMClient
from app.modules.projects.models import Project, ProjectMember, ProjectStatus
from app.modules.projects.repository import ProjectMemberRepository, ProjectRepository
from app.modules.projects.schemas import JdUploadResult
from app.modules.shadow_jobs.models import ShadowJobStatus
from app.modules.shadow_jobs.repository import ShadowJobRepository


class ProjectService:
    def __init__(self, session: AsyncSession, llm_client: ProjectsLLMClient | None = None) -> None:
        # llm_client is only needed by upload_jd -- every other method here is a plain read/write
        # and shouldn't need to inject/construct one.
        self._session = session
        self._repository = ProjectRepository(session)
        self._members = ProjectMemberRepository(session)
        self._users = UserService(session)
        self._audit = AuditService(session)
        self._llm_client = llm_client
        self._blueprints = HiringBlueprintRepository(session)
        self._alignments = HiringManagerAlignmentRepository(session)
        self._shadow_jobs = ShadowJobRepository(session)
        self._commercial = CommercialService(session)

    async def create_project(
        self,
        *,
        actor: User,
        title: str,
        department: str | None,
        status: ProjectStatus,
        hiring_manager_id: uuid.UUID | None,
        role_brief: str | None = None,
    ) -> Project:
        await self._validate_hiring_manager(actor.company_id, hiring_manager_id)
        await self._enforce_active_role_limit(actor.company_id)

        project = await self._repository.create(
            company_id=actor.company_id,
            title=title,
            department=department,
            status=status,
            hiring_manager_id=hiring_manager_id,
            created_by_id=actor.id,
            role_brief=role_brief,
        )
        # The creator (and hiring manager, if set) always get resource-level access to their own
        # project — harmless even for Owner/Admin, who bypass this check anyway, but required for
        # a Member who creates or is assigned a project to be able to see it afterwards.
        await self._members.add_member(
            company_id=actor.company_id, project_id=project.id, user_id=actor.id
        )
        if hiring_manager_id is not None:
            await self._members.add_member(
                company_id=actor.company_id, project_id=project.id, user_id=hiring_manager_id
            )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.created",
            target_type="project",
            target_id=project.id,
        )
        return project

    async def get_project(self, *, company_id: uuid.UUID, project_id: uuid.UUID) -> Project:
        project = await self._repository.get_by_id(project_id)
        if project is None or project.company_id != company_id or project.deleted_at is not None:
            raise ProjectNotFoundError()
        return project

    async def list_activity(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[AuditLog]:
        await self.get_project(company_id=company_id, project_id=project_id)
        result = await self._session.execute(
            select(AuditLog)
            .where(
                AuditLog.company_id == company_id,
                AuditLog.target_type == "project",
                AuditLog.target_id == project_id,
            )
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_projects(
        self,
        *,
        company_id: uuid.UUID,
        project_ids: list[uuid.UUID] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Project]:
        """project_ids restricts the result to that set when supplied — the API layer passes it
        for Member-role actors (their accessible project ids), leaves it None for Owner/Admin."""

        return await self._repository.list_by_company(
            company_id, project_ids=project_ids, limit=limit, offset=offset
        )

    async def add_member(self, *, actor: User, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        project = await self.get_project(company_id=actor.company_id, project_id=project_id)
        if not await self._users.is_company_member(company_id=actor.company_id, user_id=user_id):
            raise InvalidProjectMemberError()
        await self._members.add_member(
            company_id=actor.company_id, project_id=project.id, user_id=user_id
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.member_added",
            target_type="project",
            target_id=project.id,
            extra_data={"user_id": str(user_id)},
        )

    async def remove_member(
        self, *, actor: User, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        project = await self.get_project(company_id=actor.company_id, project_id=project_id)
        await self._members.remove_member(project_id=project.id, user_id=user_id)
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.member_removed",
            target_type="project",
            target_id=project.id,
            extra_data={"user_id": str(user_id)},
        )

    async def list_members(self, *, actor: User, project_id: uuid.UUID) -> list[ProjectMember]:
        await self.get_project(company_id=actor.company_id, project_id=project_id)
        return await self._members.list_members_for_project(project_id)

    async def update_project(
        self,
        *,
        actor: User,
        project_id: uuid.UUID,
        title: str | None,
        department: str | None,
        status: ProjectStatus | None,
        hiring_manager_id: uuid.UUID | None,
        hiring_manager_id_set: bool,
        role_brief: str | None = None,
        seniority: str | None = None,
        seniority_set: bool = False,
        location: str | None = None,
        location_set: bool = False,
        salary_min: int | None = None,
        salary_min_set: bool = False,
        salary_max: int | None = None,
        salary_max_set: bool = False,
    ) -> Project:
        project = await self.get_project(company_id=actor.company_id, project_id=project_id)

        if title is not None:
            project.title = title
        if department is not None:
            project.department = department
        if status is not None:
            project.status = status.value
        if role_brief is not None:
            project.role_brief = role_brief
        if hiring_manager_id_set:
            await self._validate_hiring_manager(actor.company_id, hiring_manager_id)
            project.hiring_manager_id = hiring_manager_id
        # Tri-state: these are LLM-suggested-then-user-edited values, where "clear a wrong AI
        # guess" is a real, expected action -- so an explicit null in the request must clear the
        # field, not just be ignored the way department/role_brief silently ignore a null.
        if seniority_set:
            project.seniority = seniority
        if location_set:
            project.location = location
        if salary_min_set:
            project.salary_min = salary_min
        if salary_max_set:
            project.salary_max = salary_max

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.updated",
            target_type="project",
            target_id=project.id,
        )
        return project

    async def post_to_shadow(self, *, actor: User, project_id: uuid.UUID) -> Project:
        project = await self.get_project(company_id=actor.company_id, project_id=project_id)
        blueprint, _ = await self._require_ready_to_approve(project)

        existing_job = await self._shadow_jobs.get_by_project_id(project.id)
        if existing_job is None:
            job = await self._shadow_jobs.create(
                company_id=actor.company_id,
                created_by_id=actor.id,
                title=project.title,
                department=project.department,
                seniority=project.seniority,
                employment_type="full_time",
                location=project.location,
                remote_preference=None,
                salary_min=project.salary_min,
                salary_max=project.salary_max,
                summary=blueprint.role_summary,
                description=project.role_brief or "",
                requirements=list(blueprint.must_have_qualifications),
                project_id=project.id,
            )
        else:
            job = existing_job
            job.title = project.title
            job.department = project.department
            job.seniority = project.seniority
            job.location = project.location
            job.salary_min = project.salary_min
            job.salary_max = project.salary_max
            job.summary = blueprint.role_summary
            job.description = project.role_brief or ""
            job.requirements = list(blueprint.must_have_qualifications)

        job.status = ShadowJobStatus.PUBLISHED.value
        if job.published_at is None:
            job.published_at = datetime.now(timezone.utc)

        project.status = ProjectStatus.OPEN.value

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.approved",
            target_type="project",
            target_id=project.id,
        )
        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.posted_to_shadow",
            target_type="project",
            target_id=project.id,
            extra_data={"shadow_job_id": str(job.id)},
        )
        return project

    async def save_as_draft(self, *, actor: User, project_id: uuid.UUID) -> Project:
        project = await self.get_project(company_id=actor.company_id, project_id=project_id)
        await self._require_ready_to_approve(project)

        project.status = ProjectStatus.OPEN.value

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.approved",
            target_type="project",
            target_id=project.id,
        )
        return project

    async def _require_ready_to_approve(
        self, project: Project
    ) -> tuple[HiringBlueprint, HiringManagerAlignment]:
        missing = []
        if not project.role_brief:
            missing.append("a role brief")
        blueprint = await self._blueprints.get_by_project_id(project.id)
        if blueprint is None:
            missing.append("a Hiring Blueprint")
        alignment = await self._alignments.get_by_project_id(project.id)
        if alignment is None:
            missing.append("Hiring Manager Alignment")
        if missing:
            raise ProjectNotReadyToApproveError(
                f"This role isn't ready to approve yet — missing {', '.join(missing)}."
            )
        assert blueprint is not None and alignment is not None
        return blueprint, alignment

    async def upload_jd(
        self, *, actor: User, project_id: uuid.UUID, content: bytes, content_type: str
    ) -> JdUploadResult:
        if self._llm_client is None:
            raise ValueError("upload_jd requires an llm_client")
        project = await self.get_project(company_id=actor.company_id, project_id=project_id)

        try:
            extracted_text = extract_text(content=content, content_type=content_type)
        except UnsupportedFileTypeError as exc:
            raise UnsupportedJDFileTypeError(str(exc)) from exc
        except ExtractionFailedError as exc:
            raise JDExtractionFailedError(str(exc)) from exc

        try:
            extraction = await self._llm_client.extract_role_fields(
                role_brief=extracted_text, title=project.title
            )
        except LLMRequestError as exc:
            raise RoleFieldsExtractionFailedError(str(exc)) from exc

        # Preview only -- no project mutation, no commit, no audit record. Nothing has changed
        # yet; the recruiter reviews/edits this and saves explicitly via PATCH /projects/{id}.
        return JdUploadResult(
            role_brief=extracted_text,
            seniority=extraction.seniority,
            location=extraction.location,
            salary_min=extraction.salary_min,
            salary_max=extraction.salary_max,
        )

    async def delete_project(self, *, actor: User, project_id: uuid.UUID) -> None:
        project = await self.get_project(company_id=actor.company_id, project_id=project_id)
        project.deleted_at = datetime.now(timezone.utc)

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.deleted",
            target_type="project",
            target_id=project.id,
        )

    async def _enforce_active_role_limit(self, company_id: uuid.UUID) -> None:
        """The one enforcement point for the commercial active-role limit -- see
        commercial/service.py. A null effective limit means unlimited (Scale with no override
        set yet), so it never blocks. Counted as "concurrent," not "lifetime": closing a role
        (filled/cancelled) or archiving it frees the slot immediately, per
        ProjectRepository._ACTIVE_STATUSES."""

        limit = await self._commercial.get_effective_limit_by_company_id(company_id)
        if limit is None:
            return
        active_count = await self._repository.count_active_by_company(company_id)
        if active_count >= limit:
            raise ActiveRoleLimitExceededError(
                f"You've reached your plan's limit of {limit} active role"
                f"{'s' if limit != 1 else ''}. Close a role or upgrade your plan to create another."
            )

    async def _validate_hiring_manager(
        self, company_id: uuid.UUID, hiring_manager_id: uuid.UUID | None
    ) -> None:
        if hiring_manager_id is None:
            return
        if not await self._users.is_company_member(
            company_id=company_id, user_id=hiring_manager_id
        ):
            raise InvalidHiringManagerError()
