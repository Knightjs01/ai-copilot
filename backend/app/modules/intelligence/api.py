import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.intelligence.dependencies import get_llm_client
from app.modules.intelligence.llm_client import LLMClient
from app.modules.intelligence.schemas import IntelligencePackRead
from app.modules.intelligence.service import IntelligenceService

router = APIRouter(prefix="/candidates", tags=["intelligence"])


@router.post("/{candidate_id}/intelligence-pack", response_model=IntelligencePackRead)
async def generate_intelligence_pack(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
    llm_client: LLMClient = Depends(get_llm_client),
) -> IntelligencePackRead:
    pack = await IntelligenceService(session, llm_client=llm_client).generate_pack(
        actor=actor, candidate_id=candidate_id
    )
    return IntelligencePackRead.model_validate(pack)


@router.get("/{candidate_id}/intelligence-pack", response_model=IntelligencePackRead)
async def get_intelligence_pack(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> IntelligencePackRead:
    pack = await IntelligenceService(session).get_pack(
        company_id=actor.company_id, candidate_id=candidate_id
    )
    return IntelligencePackRead.model_validate(pack)
