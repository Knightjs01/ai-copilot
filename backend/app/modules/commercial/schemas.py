import uuid

from pydantic import BaseModel, ConfigDict, Field


class CommercialPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    monthly_price_pence: int
    annual_price_pence: int
    active_role_limit: int | None
    is_active: bool


class CompanyCommercialSummary(BaseModel):
    """What a company sees about its own plan -- real numbers only, no fabricated usage. A null
    effective_limit means unlimited (a Scale company an admin hasn't set a specific number for
    yet), not "not configured" -- see CommercialService.get_effective_limit's docstring."""

    plan: CommercialPlanRead | None
    active_role_count: int
    effective_limit: int | None


class UpdateCompanyCommercialRequest(BaseModel):
    """Every field optional and applied only when present in model_fields_set, same discipline as
    CompanyUpdate -- an admin changing only the override must not silently reset the plan, and
    vice versa. active_role_limit_override: null (explicitly present) clears an existing
    override back to the plan's own default; omitting the field entirely leaves it untouched."""

    plan_code: str | None = Field(default=None)
    active_role_limit_override: int | None = Field(default=None, ge=0)
    reason: str | None = Field(default=None, max_length=1000)
