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
from app.modules.candidates.dependencies import get_file_storage
from app.modules.candidates.storage import FileStorage
from app.modules.privacy_gateway.schemas import SanitizedProfileRead
from app.modules.privacy_gateway.service import PrivacyGatewayService

router = APIRouter(prefix="/candidates", tags=["privacy-gateway"])


@router.post("/{candidate_id}/sanitize", response_model=SanitizedProfileRead)
async def sanitize_candidate(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_UPDATE)),
    session: AsyncSession = Depends(get_tenant_db),
    storage: FileStorage = Depends(get_file_storage),
) -> SanitizedProfileRead:
    profile = await PrivacyGatewayService(session, storage=storage).sanitize_candidate(
        actor=actor, candidate_id=candidate_id
    )
    return SanitizedProfileRead.model_validate(profile)


@router.get("/{candidate_id}/sanitized-profile", response_model=SanitizedProfileRead)
async def get_sanitized_profile(
    candidate_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.CANDIDATES_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> SanitizedProfileRead:
    profile = await PrivacyGatewayService(session).get_sanitized_profile(
        company_id=actor.company_id, candidate_id=candidate_id
    )
    return SanitizedProfileRead.model_validate(profile)
