from app.modules.billing.stripe_client import StripeClient

_default_stripe_client = StripeClient()


def get_stripe_client() -> StripeClient:
    """Overridable via app.dependency_overrides -- tests inject a fake that returns canned
    responses instead of calling Stripe's real API, same pattern as
    companies.dependencies.get_media_storage / candidates.dependencies.get_file_storage."""

    return _default_stripe_client
