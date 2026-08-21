import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EducationEntryRead(BaseModel):
    institution: str
    degree: str
    field: str


class IntelligencePackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    skills: list[str]
    experience_summary: str
    education: list[EducationEntryRead]
    narrative_summary: str
    highlights: list[str]
    industry: str | None
    years_experience: int | None
    model_used: str
    generated_at: datetime
