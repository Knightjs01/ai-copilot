import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.talent_pool.models import TalentPoolGrantStatus, TalentPoolScope


class TalentPoolRequestCreate(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class TalentPoolGrantRead(BaseModel):
    """Company-side view of one grant. callsign is populated only when status == granted — see
    talent_pool/__init__.py for why that's the one place PhantomPassport.callsign is ever
    surfaced to a company."""

    id: uuid.UUID
    shadow_application_id: uuid.UUID | None
    source_role_title: str
    status: TalentPoolGrantStatus
    scope: TalentPoolScope
    requested_at: datetime
    responded_at: datetime | None
    review_date: date | None
    callsign: str | None = None


class TalentPoolPoolListItem(BaseModel):
    """One row in the company's Talent Pool list — only ever built from a granted row."""

    id: uuid.UUID
    callsign: str
    headline: str | None
    seniority: str | None
    source_role_title: str
    scope: TalentPoolScope
    granted_at: datetime
    # Company-only organizational label (Phase 4) -- null means ungrouped. See
    # TalentPoolGrant.pool_name's own docstring for why this isn't a separate entity.
    pool_name: str | None = None


class TalentPoolAssignPoolRequest(BaseModel):
    grant_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    pool_name: str | None = Field(default=None, max_length=100)


class TalentPoolRenamePoolRequest(BaseModel):
    old_name: str = Field(min_length=1, max_length=100)
    new_name: str = Field(min_length=1, max_length=100)


class CandidateTalentPoolRequestRead(BaseModel):
    """What the candidate sees — company/role context plus the company's optional note, nothing
    about the request that isn't needed to decide."""

    id: uuid.UUID
    company_name: str
    source_role_title: str
    note: str | None
    status: TalentPoolGrantStatus
    scope: TalentPoolScope
    requested_at: datetime
    responded_at: datetime | None
    review_date: date | None


class TalentPoolDecision(BaseModel):
    approve: bool
    # Ignored when approve=False. The candidate's own choice of how broadly to be kept on file.
    scope: TalentPoolScope = TalentPoolScope.PROJECT_ONLY


class TalentPoolBulkRequestCreate(BaseModel):
    """Requesting Talent Pool directly from Search Candidates results -- unlike the applicant-
    scoped request above, there's no shadow_application_id here; callsigns are re-resolved
    server-side (and re-checked for eligibility) rather than trusted from a possibly-stale
    client-held search result."""

    job_id: uuid.UUID
    callsigns: list[str] = Field(min_length=1, max_length=50)
    note: str | None = Field(default=None, max_length=2000)


class TalentPoolBulkSkip(BaseModel):
    callsign: str
    reason: str


class TalentPoolBulkRequestResult(BaseModel):
    requested: list[str]
    skipped: list[TalentPoolBulkSkip]
