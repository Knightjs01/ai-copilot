import uuid

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.models import Project, ProjectMember, ProjectStatus


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: uuid.UUID,
        title: str,
        department: str | None,
        status: ProjectStatus,
        hiring_manager_id: uuid.UUID | None,
        created_by_id: uuid.UUID,
        role_brief: str | None = None,
    ) -> Project:
        project = Project(
            company_id=company_id,
            title=title,
            department=department,
            status=status.value,
            hiring_manager_id=hiring_manager_id,
            created_by_id=created_by_id,
            role_brief=role_brief,
        )
        self._session.add(project)
        await self._session.flush()
        return project

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        return await self._session.get(Project, project_id)

    async def list_by_company(
        self,
        company_id: uuid.UUID,
        *,
        project_ids: list[uuid.UUID] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Project]:
        query = select(Project).where(
            Project.company_id == company_id, Project.deleted_at.is_(None)
        )
        if project_ids is not None:
            query = query.where(Project.id.in_(project_ids))
        query = query.order_by(Project.created_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def delete_by_id(self, project_id: uuid.UUID) -> None:
        await self._session.execute(delete(Project).where(Project.id == project_id))


class ProjectMemberRepository:
    """Resource-level authorization store — see ProjectMember's docstring. Owner/Admin never
    consult this; it's only checked for Member-role actors."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_member(
        self, *, company_id: uuid.UUID, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        already = await self.is_member(project_id=project_id, user_id=user_id)
        if already:
            return
        self._session.add(
            ProjectMember(company_id=company_id, project_id=project_id, user_id=user_id)
        )
        await self._session.flush()

    async def remove_member(self, *, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(ProjectMember).where(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
        )

    async def is_member(self, *, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(
                exists().where(
                    ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
                )
            )
        )
        return bool(result.scalar_one())

    async def list_project_ids_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_members_for_project(self, project_id: uuid.UUID) -> list[ProjectMember]:
        result = await self._session.execute(
            select(ProjectMember).where(ProjectMember.project_id == project_id)
        )
        return list(result.scalars().all())

    async def delete_by_project_id(self, project_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(ProjectMember).where(ProjectMember.project_id == project_id)
        )
