import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

SourceType = Literal["must_have", "evaluation_criterion"]


class InterviewKitQuestion(BaseModel):
    source_type: SourceType
    source_text: str
    question_text: str
    follow_up_prompts: list[str]


class InterviewKitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    questions: list[InterviewKitQuestion]
    model_used: str
    generated_at: datetime
