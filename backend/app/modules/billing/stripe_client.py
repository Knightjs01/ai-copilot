import logging
from typing import Any

import httpx
import stripe

from app.core.config import get_settings
from app.modules.billing.exceptions import (
    InvalidWebhookSignatureError,
    StripeApiError,
    StripeNotConfiguredError,
)

logger = logging.getLogger("app.billing.stripe")

_BASE_URL = "https://api.stripe.com/v1"


def _flatten_params(prefix: str, value: Any) -> list[tuple[str, str]]:
    """Stripe's REST API takes form-encoded bodies with bracket-notation for nested structures
    (e.g. line_items[0][price]=price_123) -- httpx's own form encoding doesn't do this for
    nested dicts/lists, so this recursively flattens one into the list-of-pairs shape httpx's
    `data=` param accepts as-is."""
    if isinstance(value, dict):
        pairs: list[tuple[str, str]] = []
        for key, sub_value in value.items():
            pairs.extend(_flatten_params(f"{prefix}[{key}]", sub_value))
        return pairs
    if isinstance(value, list):
        pairs = []
        for index, sub_value in enumerate(value):
            pairs.extend(_flatten_params(f"{prefix}[{index}]", sub_value))
        return pairs
    return [(prefix, str(value))]


def _encode_params(params: dict[str, Any]) -> list[tuple[str, str]]:
    encoded: list[tuple[str, str]] = []
    for key, value in params.items():
        if value is None:
            continue
        encoded.extend(_flatten_params(key, value))
    return encoded


class StripeClient:
    """Direct async httpx calls against Stripe's REST API -- mirrors
    geocoding.service.GeocodingService's own external-API pattern rather than using stripe-
    python's (blocking, synchronous) HTTP client from inside async routes. stripe-python itself
    is used for exactly one thing (verify_webhook_signature below), a pure local HMAC check with
    no network call, where reusing Stripe's own well-tested verification code is safer than
    hand-rolling it."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def _require_key(self) -> str:
        if not self._settings.stripe_secret_key:
            raise StripeNotConfiguredError()
        return self._settings.stripe_secret_key

    async def _post(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        secret_key = self._require_key()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{_BASE_URL}{path}",
                auth=(secret_key, ""),
                data=_encode_params(params),  # type: ignore[arg-type]
            )
        return self._parse(response)

    async def _get(self, path: str) -> dict[str, Any]:
        secret_key = self._require_key()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{_BASE_URL}{path}", auth=(secret_key, ""))
        return self._parse(response)

    def _parse(self, response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code >= 400:
            message = body.get("error", {}).get("message", "Unknown Stripe error")
            logger.warning("Stripe API error %s: %s", response.status_code, message)
            raise StripeApiError(message)
        return body  # type: ignore[no-any-return]

    async def create_product(self, *, name: str) -> str:
        product = await self._post("/products", {"name": name})
        return product["id"]  # type: ignore[no-any-return]

    async def create_price(
        self, *, product_id: str, unit_amount_pence: int, interval: str
    ) -> str:
        price = await self._post(
            "/prices",
            {
                "product": product_id,
                "unit_amount": unit_amount_pence,
                "currency": "gbp",
                "recurring": {"interval": interval},
            },
        )
        return price["id"]  # type: ignore[no-any-return]

    async def create_customer(self, *, email: str, name: str, company_id: str) -> str:
        customer = await self._post(
            "/customers",
            {"email": email, "name": name, "metadata": {"company_id": company_id}},
        )
        return customer["id"]  # type: ignore[no-any-return]

    async def create_checkout_session(
        self,
        *,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        company_id: str,
    ) -> dict[str, Any]:
        return await self._post(
            "/checkout/sessions",
            {
                "mode": "subscription",
                "customer": customer_id,
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "client_reference_id": company_id,
            },
        )

    async def create_billing_portal_session(self, *, customer_id: str, return_url: str) -> str:
        session = await self._post(
            "/billing_portal/sessions", {"customer": customer_id, "return_url": return_url}
        )
        return session["url"]  # type: ignore[no-any-return]

    async def retrieve_subscription(self, subscription_id: str) -> dict[str, Any]:
        return await self._get(f"/subscriptions/{subscription_id}")

    async def update_subscription_price(
        self, *, subscription_id: str, new_price_id: str
    ) -> None:
        subscription = await self.retrieve_subscription(subscription_id)
        item_id = subscription["items"]["data"][0]["id"]
        await self._post(
            f"/subscriptions/{subscription_id}",
            {
                "items": [{"id": item_id, "price": new_price_id}],
                "proration_behavior": "create_prorations",
            },
        )

    def verify_webhook_signature(self, *, payload: bytes, sig_header: str) -> dict[str, Any]:
        if not self._settings.stripe_webhook_secret:
            raise StripeNotConfiguredError()
        try:
            event: dict[str, Any] = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
                payload, sig_header, self._settings.stripe_webhook_secret
            )
        except (ValueError, stripe.SignatureVerificationError) as exc:
            raise InvalidWebhookSignatureError() from exc
        return event
