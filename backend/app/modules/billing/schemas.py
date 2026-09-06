from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

BillingPeriod = Literal["monthly", "annual"]


class CompanyBillingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    billing_period: str | None
    current_period_end: datetime | None


class CheckoutSessionRequest(BaseModel):
    billing_period: BillingPeriod


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class PortalSessionResponse(BaseModel):
    portal_url: str


class SyncPlansResult(BaseModel):
    synced_plan_codes: list[str]
    already_synced_plan_codes: list[str]
