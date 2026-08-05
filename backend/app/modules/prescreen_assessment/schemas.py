import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PrescreenAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    fit_rating: str
    fit_summary: str
    strengths: list[str]
    gaps: list[str]
    suggested_questions: list[str]
    areas_to_probe: list[str]
    handoff_recommendations: list[str] | None
    model_used: str
    generated_at: datetime
