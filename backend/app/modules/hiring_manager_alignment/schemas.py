import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HiringManagerAlignmentCreate(BaseModel):
    top_requirements: list[str] = Field(min_length=1, max_length=5)


class HiringManagerAlignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    top_requirements: list[str]
    submitted_by_id: uuid.UUID
    submitted_at: datetime
