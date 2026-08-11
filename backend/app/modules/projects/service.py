import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.modules.auth.service.user_service import UserService
from app.modules.privacy_gateway.exceptions import ExtractionFailedError, UnsupportedFileTypeError
from app.modules.privacy_gateway.extraction import extract_text
from app.modules.projects.exceptions import (
    InvalidHiringManagerError,
    InvalidProjectMemberError,
    JDExtractionFailedError,
    ProjectNotFoundError,
    UnsupportedJDFileTypeError,
)
from app.modules.projects.models import Project, ProjectMember, ProjectStatus
from app.modules.projects.repository import ProjectMemberRepository, ProjectRepository


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = ProjectRepository(session)
        self._members = ProjectMemberRepository(session)
        self._users = UserService(session)
        self._audit = AuditService(session)

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

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.updated",
            target_type="project",
            target_id=project.id,
        )
        return project

    async def upload_jd(
        self, *, actor: User, project_id: uuid.UUID, content: bytes, content_type: str
    ) -> Project:
        project = await self.get_project(company_id=actor.company_id, project_id=project_id)

        try:
            extracted_text = extract_text(content=content, content_type=content_type)
        except UnsupportedFileTypeError as exc:
            raise UnsupportedJDFileTypeError(str(exc)) from exc
        except ExtractionFailedError as exc:
            raise JDExtractionFailedError(str(exc)) from exc

        project.role_brief = extracted_text

        await self._audit.record(
            company_id=actor.company_id,
            actor_user_id=actor.id,
            action="project.jd_uploaded",
            target_type="project",
            target_id=project.id,
        )
        return project

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

    async def _validate_hiring_manager(
        self, company_id: uuid.UUID, hiring_manager_id: uuid.UUID | None
    ) -> None:
        if hiring_manager_id is None:
            return
        if not await self._users.is_company_member(
            company_id=company_id, user_id=hiring_manager_id
        ):
            raise InvalidHiringManagerError()
