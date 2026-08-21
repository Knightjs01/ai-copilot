import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.authorization import actor_has_org_wide_access
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.projects.dependencies import get_projects_llm_client, require_project_access
from app.modules.projects.llm_client import ProjectsLLMClient
from app.modules.projects.repository import ProjectMemberRepository
from app.modules.projects.schemas import (
    JdUploadResult,
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectRead,
    ProjectUpdate,
)
from app.modules.projects.service import ProjectService

router = APIRouter(
    prefix="/projects", tags=["projects"], dependencies=[Depends(require_mfa_enrolled)]
)


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
    # Owner/Admin see every company project; a Member only sees projects they've been added to
    # via ProjectMember — resource-level scoping, not just the role check above.
    project_ids: list[uuid.UUID] | None = None
    if not await actor_has_org_wide_access(session, actor.id):
        project_ids = await ProjectMemberRepository(session).list_project_ids_for_user(actor.id)

    projects = await ProjectService(session).list_projects(
        company_id=actor.company_id, project_ids=project_ids, limit=limit, offset=offset
    )
    return [ProjectRead.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    __: None = Depends(require_project_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> ProjectRead:
    project = await ProjectService(session).get_project(
        company_id=actor.company_id, project_id=project_id
    )
    return ProjectRead.model_validate(project)


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
async def list_project_members(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    __: None = Depends(require_project_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[ProjectMemberRead]:
    members = await ProjectService(session).list_members(actor=actor, project_id=project_id)
    return [ProjectMemberRead.model_validate(m) for m in members]


@router.post(
    "/{project_id}/members", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED
)
async def add_project_member(
    project_id: uuid.UUID,
    body: ProjectMemberCreate,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_UPDATE)),
    __: None = Depends(require_project_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> ProjectMemberRead:
    await ProjectService(session).add_member(
        actor=actor, project_id=project_id, user_id=body.user_id
    )
    members = await ProjectMemberRepository(session).list_members_for_project(project_id)
    added = next(m for m in members if m.user_id == body.user_id)
    return ProjectMemberRead.model_validate(added)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_UPDATE)),
    __: None = Depends(require_project_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await ProjectService(session).remove_member(actor=actor, project_id=project_id, user_id=user_id)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_UPDATE)),
    __: None = Depends(require_project_access),
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
        seniority=body.seniority,
        seniority_set="seniority" in fields_set,
        location=body.location,
        location_set="location" in fields_set,
        salary_min=body.salary_min,
        salary_min_set="salary_min" in fields_set,
        salary_max=body.salary_max,
        salary_max_set="salary_max" in fields_set,
    )
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/jd", response_model=JdUploadResult)
async def upload_jd(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_UPDATE)),
    __: None = Depends(require_project_access),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: ProjectsLLMClient = Depends(get_projects_llm_client),
) -> JdUploadResult:
    content = await file.read()
    return await ProjectService(session, llm_client=llm_client).upload_jd(
        actor=actor,
        project_id=project_id,
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_DELETE)),
    __: None = Depends(require_project_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await ProjectService(session).delete_project(actor=actor, project_id=project_id)
