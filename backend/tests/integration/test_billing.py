import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import update

from app.db.base import auth_session_factory
from app.modules.commercial.models import CommercialPlan
from tests.conftest import CapturingEmailSender, FakeStripeClient
from tests.integration.helpers import (
    auth_headers,
    invite_and_accept,
    platform_admin_headers,
    signup,
)


@pytest_asyncio.fixture(autouse=True)
async def _reset_stripe_sync_state() -> None:
    """commercial_plans is static seed data -- _clean_tables deliberately never truncates it
    between tests (same reasoning it already applies to permissions/roles), since it's shared
    system catalog data, not per-test tenant data. But that means whichever test syncs it to
    Stripe first leaves every test that runs after it in the same suite invocation seeing
    already-synced plans. Reset the three Stripe columns back to NULL before each test in this
    file so every test starts from the same "not yet synced" baseline regardless of run order."""

    async with auth_session_factory() as session:
        await session.execute(
            update(CommercialPlan).values(
                stripe_product_id=None, stripe_price_id_monthly=None, stripe_price_id_annual=None
            )
        )
        await session.commit()


async def _sync_plans(client: AsyncClient) -> None:
    admin_headers = await platform_admin_headers(client)
    response = await client.post(
        "/api/v1/platform-admin/billing/sync-plans", headers=admin_headers
    )
    assert response.status_code == 200, response.text


async def _set_plan(client: AsyncClient, *, company_id: str, plan_code: str) -> None:
    admin_headers = await platform_admin_headers(client)
    response = await client.post(
        f"/api/v1/platform-admin/commercial/companies/{company_id}",
        json={"plan_code": plan_code},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text


async def test_sync_plans_creates_stripe_products_and_prices(
    client: AsyncClient, fake_stripe_client: FakeStripeClient
) -> None:
    admin_headers = await platform_admin_headers(client)
    response = await client.post(
        "/api/v1/platform-admin/billing/sync-plans", headers=admin_headers
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert sorted(body["synced_plan_codes"]) == ["core", "growth", "scale"]
    assert body["already_synced_plan_codes"] == []
    # One product + two prices (monthly, annual) per plan.
    assert len(fake_stripe_client.created_products) == 3
    assert len(fake_stripe_client.created_prices) == 6


async def test_sync_plans_is_idempotent(
    client: AsyncClient, fake_stripe_client: FakeStripeClient
) -> None:
    await _sync_plans(client)
    admin_headers = await platform_admin_headers(client)
    response = await client.post(
        "/api/v1/platform-admin/billing/sync-plans", headers=admin_headers
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["synced_plan_codes"] == []
    assert sorted(body["already_synced_plan_codes"]) == ["core", "growth", "scale"]
    # No new Stripe objects created the second time around.
    assert len(fake_stripe_client.created_products) == 3
    assert len(fake_stripe_client.created_prices) == 6


async def test_checkout_fails_until_plan_synced(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@billing-unsynced.com")
    headers = auth_headers(owner["access_token"])

    response = await client.post(
        "/api/v1/companies/me/billing/checkout",
        json={"billing_period": "monthly"},
        headers=headers,
    )
    assert response.status_code == 409, response.text


async def test_checkout_creates_customer_and_returns_checkout_url(
    client: AsyncClient, fake_stripe_client: FakeStripeClient
) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-checkout.com")
    headers = auth_headers(owner["access_token"])

    response = await client.post(
        "/api/v1/companies/me/billing/checkout",
        json={"billing_period": "monthly"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    checkout_url = response.json()["checkout_url"]
    assert checkout_url.startswith("https://checkout.stripe.test/")
    assert len(fake_stripe_client.created_customers) == 1
    email, name, company_id = fake_stripe_client.created_customers[0]
    assert email == "owner@billing-checkout.com"
    assert company_id  # a real company id was threaded through, not blank

    # Starting a second checkout for the same company must reuse the same Stripe customer,
    # not create a duplicate.
    second = await client.post(
        "/api/v1/companies/me/billing/checkout",
        json={"billing_period": "annual"},
        headers=headers,
    )
    assert second.status_code == 200, second.text
    assert len(fake_stripe_client.created_customers) == 1


async def test_recruiter_cannot_manage_billing(
    client: AsyncClient, sent_emails: CapturingEmailSender
) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-permissions.com")
    owner_headers = auth_headers(owner["access_token"])
    member = await invite_and_accept(
        client,
        inviter_headers=owner_headers,
        email="member@billing-permissions.com",
        role="Recruiter",
        sent_emails=sent_emails,
    )
    member_headers = auth_headers(member["access_token"])

    response = await client.post(
        "/api/v1/companies/me/billing/checkout",
        json={"billing_period": "monthly"},
        headers=member_headers,
    )
    assert response.status_code == 403


async def test_billing_portal_requires_a_customer_first(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@billing-noportal.com")
    headers = auth_headers(owner["access_token"])

    response = await client.post("/api/v1/companies/me/billing/portal", headers=headers)
    assert response.status_code == 409, response.text


async def test_billing_portal_after_checkout_started(
    client: AsyncClient, fake_stripe_client: FakeStripeClient
) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-portal.com")
    headers = auth_headers(owner["access_token"])
    await client.post(
        "/api/v1/companies/me/billing/checkout",
        json={"billing_period": "monthly"},
        headers=headers,
    )

    response = await client.post("/api/v1/companies/me/billing/portal", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["portal_url"].startswith("https://billing.stripe.test/")
    assert len(fake_stripe_client.portal_session_customer_ids) == 1


async def test_webhook_missing_signature_returns_400(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/webhooks/stripe",
        json={"type": "checkout.session.completed", "data": {"object": {}}},
    )
    assert response.status_code == 400


async def test_webhook_invalid_signature_returns_400(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/webhooks/stripe",
        json={"type": "checkout.session.completed", "data": {"object": {}}},
        headers={"stripe-signature": "not-the-right-signature"},
    )
    assert response.status_code == 400


async def test_webhook_checkout_completed_activates_billing(client: AsyncClient) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-webhook-activate.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    webhook = await client.post(
        "/api/v1/webhooks/stripe",
        json={
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": company_id,
                    "customer": "cus_real_123",
                    "subscription": "sub_real_123",
                }
            },
        },
        headers={"stripe-signature": "test-signature"},
    )
    assert webhook.status_code == 204, webhook.text

    billing = await client.get("/api/v1/companies/me/billing", headers=headers)
    assert billing.status_code == 200, billing.text
    assert billing.json()["status"] == "active"


async def test_webhook_subscription_updated_sets_past_due(client: AsyncClient) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-webhook-pastdue.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    await client.post(
        "/api/v1/webhooks/stripe",
        json={
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": company_id,
                    "customer": "cus_pastdue_123",
                    "subscription": "sub_pastdue_123",
                }
            },
        },
        headers={"stripe-signature": "test-signature"},
    )

    webhook = await client.post(
        "/api/v1/webhooks/stripe",
        json={
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "customer": "cus_pastdue_123",
                    "status": "past_due",
                    "current_period_end": 1_800_000_000,
                }
            },
        },
        headers={"stripe-signature": "test-signature"},
    )
    assert webhook.status_code == 204, webhook.text

    billing = await client.get("/api/v1/companies/me/billing", headers=headers)
    assert billing.json()["status"] == "past_due"
    assert billing.json()["current_period_end"] is not None


async def test_webhook_subscription_deleted_cancels(client: AsyncClient) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-webhook-cancel.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    await client.post(
        "/api/v1/webhooks/stripe",
        json={
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": company_id,
                    "customer": "cus_cancel_123",
                    "subscription": "sub_cancel_123",
                }
            },
        },
        headers={"stripe-signature": "test-signature"},
    )

    webhook = await client.post(
        "/api/v1/webhooks/stripe",
        json={
            "type": "customer.subscription.deleted",
            "data": {"object": {"customer": "cus_cancel_123"}},
        },
        headers={"stripe-signature": "test-signature"},
    )
    assert webhook.status_code == 204, webhook.text

    billing = await client.get("/api/v1/companies/me/billing", headers=headers)
    assert billing.json()["status"] == "canceled"


async def test_webhook_payment_failed_sets_past_due_and_notifies_admins(
    client: AsyncClient,
) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-webhook-failed.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    await client.post(
        "/api/v1/webhooks/stripe",
        json={
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": company_id,
                    "customer": "cus_failed_123",
                    "subscription": "sub_failed_123",
                }
            },
        },
        headers={"stripe-signature": "test-signature"},
    )

    webhook = await client.post(
        "/api/v1/webhooks/stripe",
        json={
            "type": "invoice.payment_failed",
            "data": {"object": {"customer": "cus_failed_123"}},
        },
        headers={"stripe-signature": "test-signature"},
    )
    assert webhook.status_code == 204, webhook.text

    billing = await client.get("/api/v1/companies/me/billing", headers=headers)
    assert billing.json()["status"] == "past_due"

    admin_headers = await platform_admin_headers(client)
    notifications = await client.get(
        "/api/v1/platform-admin/notifications", headers=admin_headers
    )
    assert notifications.status_code == 200, notifications.text
    actions = [item["action"] for item in notifications.json()["items"]]
    assert "company.billing_past_due" in actions


async def test_changing_plan_syncs_existing_subscription_price(
    client: AsyncClient, fake_stripe_client: FakeStripeClient
) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-plan-change.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    # Give the company a real, active Stripe subscription first.
    await client.post(
        "/api/v1/webhooks/stripe",
        json={
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": company_id,
                    "customer": "cus_planchange_123",
                    "subscription": "sub_planchange_123",
                }
            },
        },
        headers={"stripe-signature": "test-signature"},
    )
    assert fake_stripe_client.subscription_price_updates == []

    await _set_plan(client, company_id=company_id, plan_code="growth")

    assert len(fake_stripe_client.subscription_price_updates) == 1
    subscription_id, _new_price_id = fake_stripe_client.subscription_price_updates[0]
    assert subscription_id == "sub_planchange_123"


async def test_changing_plan_is_a_noop_when_no_subscription_exists(
    client: AsyncClient, fake_stripe_client: FakeStripeClient
) -> None:
    await _sync_plans(client)
    owner = await signup(client, email="owner@billing-no-subscription.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    await _set_plan(client, company_id=company_id, plan_code="growth")

    assert fake_stripe_client.subscription_price_updates == []


async def test_admin_company_detail_includes_billing_status(client: AsyncClient) -> None:
    owner = await signup(client, email="owner@billing-admindetail.com")
    headers = auth_headers(owner["access_token"])
    me = await client.get("/api/v1/companies/me", headers=headers)
    company_id = me.json()["id"]

    admin_headers = await platform_admin_headers(client)
    detail = await client.get(
        f"/api/v1/companies/{company_id}/detail", headers=admin_headers
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["billing_status"] == "not_started"
