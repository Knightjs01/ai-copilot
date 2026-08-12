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
from app.modules.hiring_blueprint.dependencies import get_hiring_blueprint_llm_client
from app.modules.hiring_blueprint.llm_client import HiringBlueprintLLMClient
from app.modules.hiring_blueprint.schemas import HiringBlueprintRead
from app.modules.hiring_blueprint.service import HiringBlueprintService

router = APIRouter(
    prefix="/projects", tags=["hiring-blueprint"], dependencies=[Depends(require_mfa_enrolled)]
)


@router.post("/{project_id}/hiring-blueprint", response_model=HiringBlueprintRead)
async def generate_hiring_blueprint(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: HiringBlueprintLLMClient = Depends(get_hiring_blueprint_llm_client),
) -> HiringBlueprintRead:
    blueprint = await HiringBlueprintService(session, llm_client=llm_client).generate_blueprint(
        actor=actor, project_id=project_id
    )
    return HiringBlueprintRead.model_validate(blueprint)


@router.get("/{project_id}/hiring-blueprint", response_model=HiringBlueprintRead)
async def get_hiring_blueprint(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> HiringBlueprintRead:
    blueprint = await HiringBlueprintService(session).get_blueprint(
        company_id=actor.company_id, project_id=project_id
    )
    return HiringBlueprintRead.model_validate(blueprint)
