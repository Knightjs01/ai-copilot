import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
    require_step_up,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.identity_vault.schemas import (
    IdentitySnapshot,
    RevealCloseRequest,
    RevealRequest,
    VaultDashboardStats,
    VaultFieldsUpdate,
    VaultListItem,
)
from app.modules.identity_vault.service import IdentityVaultService

router = APIRouter(
    prefix="/identity-vault",
    tags=["identity-vault"],
    dependencies=[Depends(require_mfa_enrolled)],
)


@router.post("/candidates/{candidate_id}/reveal", response_model=IdentitySnapshot)
async def reveal_identity(
    candidate_id: uuid.UUID,
    body: RevealRequest,
    request: Request,
    actor: User = Depends(require_step_up),
    _: CurrentUser = Depends(require_permission(Permissions.IDENTITY_VAULT_REVEAL)),
    session: AsyncSession = Depends(get_tenant_db),
) -> IdentitySnapshot:
    return await IdentityVaultService(session).reveal_identity(
        actor=actor,
        candidate_id=candidate_id,
        reason=body.reason,
        ip_address=request.client.host if request.client else None,
    )


@router.post("/reveal-events/{event_id}/close", status_code=status.HTTP_204_NO_CONTENT)
async def close_reveal(
    event_id: uuid.UUID,
    body: RevealCloseRequest,
    _actor: User = Depends(get_current_user_model),
    __: CurrentUser = Depends(require_permission(Permissions.IDENTITY_VAULT_REVEAL)),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await IdentityVaultService(session).close_reveal(
        reveal_event_id=event_id, duration_seconds=body.duration_seconds
    )


@router.patch("/candidates/{candidate_id}", response_model=VaultFieldsUpdate)
async def update_vault_fields(
    candidate_id: uuid.UUID,
    body: VaultFieldsUpdate,
    _actor: User = Depends(get_current_user_model),
    __: CurrentUser = Depends(require_permission(Permissions.IDENTITY_VAULT_REVEAL)),
    session: AsyncSession = Depends(get_tenant_db),
) -> VaultFieldsUpdate:
    await IdentityVaultService(session).update_vault_fields(
        candidate_id=candidate_id,
        location=body.location,
        current_employer=body.current_employer,
        current_title=body.current_title,
        linkedin_url=body.linkedin_url,
    )
    return body


@router.get("/projects/{project_id}", response_model=list[VaultListItem])
async def list_vault_for_project(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.IDENTITY_VAULT_REVEAL)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[VaultListItem]:
    return await IdentityVaultService(session).list_vault_for_project(
        company_id=actor.company_id, project_id=project_id
    )


@router.get("/projects/{project_id}/dashboard", response_model=VaultDashboardStats)
async def get_dashboard(
    project_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.IDENTITY_VAULT_REVEAL)),
    session: AsyncSession = Depends(get_tenant_db),
) -> VaultDashboardStats:
    return await IdentityVaultService(session).get_dashboard_stats(
        company_id=actor.company_id, project_id=project_id
    )
