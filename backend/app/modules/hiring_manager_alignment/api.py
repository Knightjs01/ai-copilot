import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.hiring_manager_alignment.schemas import (
    HiringManagerAlignmentCreate,
    HiringManagerAlignmentRead,
)
from app.modules.hiring_manager_alignment.service import HiringManagerAlignmentService
from app.modules.projects.dependencies import require_project_access

router = APIRouter(
    prefix="/projects",
    tags=["hiring-manager-alignment"],
    dependencies=[Depends(require_mfa_enrolled)],
)


@router.put("/{project_id}/hiring-manager-alignment", response_model=HiringManagerAlignmentRead)
async def submit_hiring_manager_alignment(
    project_id: uuid.UUID,
    body: HiringManagerAlignmentCreate,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.HIRING_MANAGER_ALIGNMENT_SUBMIT)),
    __: None = Depends(require_project_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> HiringManagerAlignmentRead:
    alignment = await HiringManagerAlignmentService(session).submit_alignment(
        actor=actor, project_id=project_id, top_requirements=body.top_requirements
    )
    return HiringManagerAlignmentRead.model_validate(alignment)


@router.get("/{project_id}/hiring-manager-alignment", response_model=HiringManagerAlignmentRead)
async def get_hiring_manager_alignment(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    __: None = Depends(require_project_access),
    session: AsyncSession = Depends(get_tenant_db),
) -> HiringManagerAlignmentRead:
    alignment = await HiringManagerAlignmentService(session).get_alignment(
        company_id=actor.company_id, project_id=project_id
    )
    return HiringManagerAlignmentRead.model_validate(alignment)
