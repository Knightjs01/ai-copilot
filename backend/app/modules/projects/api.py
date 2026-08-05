import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.projects.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from app.modules.projects.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_CREATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ProjectRead:
    project = await ProjectService(session).create_project(
        actor=actor,
        title=body.title,
        department=body.department,
        status=body.status,
        hiring_manager_id=body.hiring_manager_id,
        role_brief=body.role_brief,
    )
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ProjectRead]:
    projects = await ProjectService(session).list_projects(
        company_id=actor.company_id, limit=limit, offset=offset
    )
    return [ProjectRead.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ProjectRead:
    project = await ProjectService(session).get_project(
        company_id=actor.company_id, project_id=project_id
    )
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> ProjectRead:
    fields_set = body.model_fields_set
    project = await ProjectService(session).update_project(
        actor=actor,
        project_id=project_id,
        title=body.title,
        department=body.department,
        status=body.status,
        hiring_manager_id=body.hiring_manager_id,
        hiring_manager_id_set="hiring_manager_id" in fields_set,
        role_brief=body.role_brief,
    )
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_DELETE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await ProjectService(session).delete_project(actor=actor, project_id=project_id)
