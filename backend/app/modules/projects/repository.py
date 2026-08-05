import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.models import Project, ProjectStatus


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
    ) -> Project:
        project = Project(
            company_id=company_id,
            title=title,
            department=department,
            status=status.value,
            hiring_manager_id=hiring_manager_id,
            created_by_id=created_by_id,
        )
        self._session.add(project)
        await self._session.flush()
        return project

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        return await self._session.get(Project, project_id)

    async def list_by_company(
        self, company_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[Project]:
        result = await self._session.execute(
            select(Project)
            .where(Project.company_id == company_id, Project.deleted_at.is_(None))
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
