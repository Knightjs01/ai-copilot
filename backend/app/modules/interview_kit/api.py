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
from app.modules.interview_kit.dependencies import get_interview_kit_llm_client
from app.modules.interview_kit.llm_client import InterviewKitLLMClient
from app.modules.interview_kit.schemas import InterviewKitRead
from app.modules.interview_kit.service import InterviewKitService

router = APIRouter(
    prefix="/projects", tags=["interview-kit"], dependencies=[Depends(require_mfa_enrolled)]
)


@router.post("/{project_id}/interview-kit", response_model=InterviewKitRead)
async def generate_interview_kit(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: InterviewKitLLMClient = Depends(get_interview_kit_llm_client),
) -> InterviewKitRead:
    kit = await InterviewKitService(session, llm_client=llm_client).generate_kit(
        actor=actor, project_id=project_id
    )
    return InterviewKitRead.model_validate(kit)


@router.get("/{project_id}/interview-kit", response_model=InterviewKitRead)
async def get_interview_kit(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.PROJECTS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> InterviewKitRead:
    kit = await InterviewKitService(session).get_kit(
        company_id=actor.company_id, project_id=project_id
    )
    return InterviewKitRead.model_validate(kit)
