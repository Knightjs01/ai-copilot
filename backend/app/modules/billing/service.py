import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.billing.exceptions import NoStripeCustomerError, PlanNotSyncedToStripeError
from app.modules.billing.models import CompanyBilling, CompanyBillingStatus
from app.modules.billing.schemas import BillingPeriod, SyncPlansResult
from app.modules.billing.stripe_client import StripeClient
from app.modules.commercial.models import CommercialPlan
from app.modules.commercial.repository import CommercialPlanRepository
from app.modules.companies.models import Company
from app.modules.platform_admin.notification_service import PlatformAdminNotificationService
from app.modules.platform_admin.permissions import PlatformAdminPermissions

_INTERVAL_BY_PERIOD = {"monthly": "month", "annual": "year"}
_PRICE_COLUMN_BY_PERIOD = {
    "monthly": "stripe_price_id_monthly",
    "annual": "stripe_price_id_annual",
}


class CompanyBillingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_company_id(self, company_id: uuid.UUID) -> CompanyBilling | None:
        result = await self._session.execute(
            select(CompanyBilling).where(CompanyBilling.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> CompanyBilling | None:
        result = await self._session.execute(
            select(CompanyBilling).where(CompanyBilling.stripe_customer_id == stripe_customer_id)
        )
        return result.scalar_one_or_none()

    async def create(self, *, company_id: uuid.UUID) -> CompanyBilling:
        billing = CompanyBilling(company_id=company_id)
        self._session.add(billing)
        await self._session.flush()
        return billing


class BillingService:
    """Real Stripe subscription billing on top of the existing admin-assigned CommercialPlan
    catalog. Deliberately does not touch who can create a company or which plan they start on --
    see the plan this shipped under for why that stays admin-gated exactly as it already is."""

    def __init__(self, session: AsyncSession, *, stripe: StripeClient | None = None) -> None:
        self._session = session
        self._settings = get_settings()
        self._billing = CompanyBillingRepository(session)
        self._plans = CommercialPlanRepository(session)
        # Overridable so callers (routes via Depends(get_stripe_client), or CommercialService
        # composing this internally) can thread through a test double -- same "swappable
        # dependency must be threaded through every level of composition" fix already applied to
        # PrivacyGatewayService/CandidateService's storage param.
        self._stripe = stripe or StripeClient()
        self._notifications = PlatformAdminNotificationService(session)

    async def ensure_plans_synced_to_stripe(self) -> SyncPlansResult:
        plans = await self._plans.list_active()
        synced: list[str] = []
        already_synced: list[str] = []
        for plan in plans:
            if plan.stripe_price_id_monthly and plan.stripe_price_id_annual:
                already_synced.append(plan.code)
                continue

            product_id = plan.stripe_product_id
            if product_id is None:
                product_id = await self._stripe.create_product(name=plan.name)
                plan.stripe_product_id = product_id

            if plan.stripe_price_id_monthly is None:
                plan.stripe_price_id_monthly = await self._stripe.create_price(
                    product_id=product_id,
                    unit_amount_pence=plan.monthly_price_pence,
                    interval="month",
                )
            if plan.stripe_price_id_annual is None:
                plan.stripe_price_id_annual = await self._stripe.create_price(
                    product_id=product_id,
                    unit_amount_pence=plan.annual_price_pence,
                    interval="year",
                )
            synced.append(plan.code)

        await self._session.flush()
        return SyncPlansResult(synced_plan_codes=synced, already_synced_plan_codes=already_synced)

    async def get_billing_status(self, company_id: uuid.UUID) -> CompanyBilling | None:
        return await self._billing.get_by_company_id(company_id)

    async def _get_or_create_billing_row(self, company_id: uuid.UUID) -> CompanyBilling:
        billing = await self._billing.get_by_company_id(company_id)
        if billing is None:
            billing = await self._billing.create(company_id=company_id)
        return billing

    async def _get_plan_for_company(self, company: Company) -> CommercialPlan:
        if company.commercial_plan_id is None:
            raise PlanNotSyncedToStripeError("This company has no commercial plan assigned")
        plan = await self._plans.get_by_id(company.commercial_plan_id)
        if plan is None:
            raise PlanNotSyncedToStripeError("This company's commercial plan no longer exists")
        return plan

    async def start_checkout(
        self, *, company: Company, owner_email: str, billing_period: BillingPeriod
    ) -> str:
        plan = await self._get_plan_for_company(company)
        price_id = getattr(plan, _PRICE_COLUMN_BY_PERIOD[billing_period])
        if price_id is None:
            raise PlanNotSyncedToStripeError()

        billing = await self._get_or_create_billing_row(company.id)
        if billing.stripe_customer_id is None:
            billing.stripe_customer_id = await self._stripe.create_customer(
                email=owner_email, name=company.name, company_id=str(company.id)
            )
            await self._session.flush()

        base_url = self._settings.frontend_base_url
        session = await self._stripe.create_checkout_session(
            customer_id=billing.stripe_customer_id,
            price_id=price_id,
            success_url=f"{base_url}/company?billing=success",
            cancel_url=f"{base_url}/company?billing=cancelled",
            company_id=str(company.id),
        )
        return session["url"]  # type: ignore[no-any-return]

    async def start_portal_session(self, *, company: Company) -> str:
        billing = await self._billing.get_by_company_id(company.id)
        if billing is None or billing.stripe_customer_id is None:
            raise NoStripeCustomerError()
        base_url = self._settings.frontend_base_url
        return await self._stripe.create_billing_portal_session(
            customer_id=billing.stripe_customer_id, return_url=f"{base_url}/company"
        )

    async def sync_subscription_price(self, *, company: Company, billing_period: BillingPeriod | None = None) -> None:
        """Called from CommercialService.set_company_commercial when an admin changes a
        company's plan -- if that company already has an active Stripe subscription, keep it in
        sync rather than leaving it billing the old plan's price forever."""
        billing = await self._billing.get_by_company_id(company.id)
        if billing is None or billing.stripe_subscription_id is None:
            return
        plan = await self._get_plan_for_company(company)
        period = billing_period or billing.billing_period or "monthly"
        price_id = getattr(plan, _PRICE_COLUMN_BY_PERIOD[period])
        if price_id is None:
            return
        await self._stripe.update_subscription_price(
            subscription_id=billing.stripe_subscription_id, new_price_id=price_id
        )

    async def handle_webhook(self, *, payload: bytes, sig_header: str) -> None:
        event = self._stripe.verify_webhook_signature(payload=payload, sig_header=sig_header)
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(data)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(data)
        elif event_type == "invoice.payment_failed":
            await self._handle_payment_failed(data)

    async def _handle_checkout_completed(self, session: dict[str, Any]) -> None:
        company_id_raw = session.get("client_reference_id")
        if not company_id_raw:
            return
        company_id = uuid.UUID(company_id_raw)
        billing = await self._get_or_create_billing_row(company_id)
        billing.stripe_customer_id = session.get("customer") or billing.stripe_customer_id
        billing.stripe_subscription_id = session.get("subscription")
        billing.status = CompanyBillingStatus.ACTIVE.value
        await self._session.flush()

    async def _handle_subscription_updated(self, subscription: dict[str, Any]) -> None:
        billing = await self._billing.get_by_stripe_customer_id(subscription["customer"])
        if billing is None:
            return
        status = subscription.get("status")
        billing.status = (
            CompanyBillingStatus.ACTIVE.value
            if status in ("active", "trialing")
            else CompanyBillingStatus.PAST_DUE.value
            if status == "past_due"
            else billing.status
        )
        period_end = subscription.get("current_period_end")
        if period_end is not None:
            billing.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
        await self._session.flush()

    async def _handle_subscription_deleted(self, subscription: dict[str, Any]) -> None:
        billing = await self._billing.get_by_stripe_customer_id(subscription["customer"])
        if billing is None:
            return
        billing.status = CompanyBillingStatus.CANCELED.value
        await self._session.flush()

    async def _handle_payment_failed(self, invoice: dict[str, Any]) -> None:
        customer_id = invoice.get("customer")
        if not customer_id:
            return
        billing = await self._billing.get_by_stripe_customer_id(customer_id)
        if billing is None:
            return
        billing.status = CompanyBillingStatus.PAST_DUE.value
        await self._session.flush()

        company = await self._session.get(Company, billing.company_id)
        company_name = company.name if company is not None else "A company"
        await self._notifications.notify(
            action="company.billing_past_due",
            title="Payment failed",
            body=f"{company_name}'s subscription payment failed and needs attention",
            target_type="company",
            target_id=billing.company_id,
            required_permission=PlatformAdminPermissions.COMPANIES_VIEW,
        )
