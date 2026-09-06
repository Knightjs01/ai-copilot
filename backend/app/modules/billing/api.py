from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user_model,
    get_tenant_db,
    require_mfa_enrolled,
    require_permission,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.billing.dependencies import get_stripe_client
from app.modules.billing.exceptions import InvalidWebhookSignatureError
from app.modules.billing.models import CompanyBillingStatus
from app.modules.billing.schemas import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CompanyBillingRead,
    PortalSessionResponse,
    SyncPlansResult,
)
from app.modules.billing.service import BillingService
from app.modules.billing.stripe_client import StripeClient
from app.modules.companies.exceptions import CompanyNotFoundError
from app.modules.companies.service import CompanyService
from app.modules.platform_admin.dependencies import (
    PlatformAdminContext,
    require_platform_admin_permission,
)
from app.modules.platform_admin.permissions import PlatformAdminPermissions

router = APIRouter(
    prefix="/companies", tags=["billing"], dependencies=[Depends(require_mfa_enrolled)]
)

admin_router = APIRouter(prefix="/platform-admin/billing", tags=["billing"])

webhook_router = APIRouter(tags=["billing"])


@router.get("/me/billing", response_model=CompanyBillingRead)
async def get_my_billing(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
) -> CompanyBillingRead:
    billing = await BillingService(session).get_billing_status(actor.company_id)
    if billing is None:
        return CompanyBillingRead(
            status=CompanyBillingStatus.NOT_STARTED.value,
            billing_period=None,
            current_period_end=None,
        )
    return CompanyBillingRead.model_validate(billing)


@router.post("/me/billing/checkout", response_model=CheckoutSessionResponse)
async def start_my_checkout(
    body: CheckoutSessionRequest,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
    stripe: StripeClient = Depends(get_stripe_client),
) -> CheckoutSessionResponse:
    company_service = CompanyService(session)
    company = await company_service.get_company(actor.company_id)
    if company is None:
        raise CompanyNotFoundError()
    checkout_url = await BillingService(session, stripe=stripe).start_checkout(
        company=company, owner_email=actor.email, billing_period=body.billing_period
    )
    return CheckoutSessionResponse(checkout_url=checkout_url)


@router.post("/me/billing/portal", response_model=PortalSessionResponse)
async def start_my_billing_portal(
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.COMPANY_MANAGE_SETTINGS)),
    session: AsyncSession = Depends(get_tenant_db),
    stripe: StripeClient = Depends(get_stripe_client),
) -> PortalSessionResponse:
    company_service = CompanyService(session)
    company = await company_service.get_company(actor.company_id)
    if company is None:
        raise CompanyNotFoundError()
    portal_url = await BillingService(session, stripe=stripe).start_portal_session(company=company)
    return PortalSessionResponse(portal_url=portal_url)


@admin_router.post("/sync-plans", response_model=SyncPlansResult)
async def sync_plans_to_stripe(
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.COMMERCIAL_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
    stripe: StripeClient = Depends(get_stripe_client),
) -> SyncPlansResult:
    return await BillingService(session, stripe=stripe).ensure_plans_synced_to_stripe()


@webhook_router.post("/webhooks/stripe", status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
    stripe: StripeClient = Depends(get_stripe_client),
) -> None:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")
    try:
        await BillingService(session, stripe=stripe).handle_webhook(
            payload=payload, sig_header=sig_header
        )
    except InvalidWebhookSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
