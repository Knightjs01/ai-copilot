import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HiringBlueprintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    role_summary: str
    key_responsibilities: list[str]
    must_have_qualifications: list[str]
    nice_to_have_qualifications: list[str]
    evaluation_criteria: list[str]
    model_used: str
    generated_at: datetime
