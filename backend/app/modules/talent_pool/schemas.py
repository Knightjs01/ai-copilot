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
