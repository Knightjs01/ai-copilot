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
from app.modules.historic_vault.schemas import HistoricVaultOverview
from app.modules.historic_vault.service import HistoricVaultService

router = APIRouter(
    prefix="/historic-vault", tags=["historic-vault"], dependencies=[Depends(require_mfa_enrolled)]
)


@router.get("", response_model=HistoricVaultOverview)
async def get_historic_vault(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.HISTORIC_VAULT_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> HistoricVaultOverview:
    return await HistoricVaultService(session).get_overview(company_id=actor.company_id)
