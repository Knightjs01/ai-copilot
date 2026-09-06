from app.core.exceptions import AppError


class BillingError(AppError):
    status_code = 400
    detail = "Billing error"


class StripeNotConfiguredError(BillingError):
    status_code = 503
    detail = "Billing is not configured yet"


class NoStripeCustomerError(BillingError):
    status_code = 409
    detail = "No billing account exists for this company yet — start a checkout first"


class PlanNotSyncedToStripeError(BillingError):
    status_code = 409
    detail = "This plan has not been synced to Stripe yet"


class StripeApiError(BillingError):
    status_code = 502
    detail = "Stripe request failed"


class InvalidWebhookSignatureError(BillingError):
    status_code = 400
    detail = "Invalid webhook signature"
