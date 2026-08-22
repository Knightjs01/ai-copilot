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
    # Whether the hiring team has chosen this question for the finalized kit — starts false on
    # every (re)generation, since the point is the team curating down from the suggested list,
    # not everything being included by default.
    included: bool = False


class InterviewKitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    questions: list[InterviewKitQuestion]
    model_used: str
    generated_at: datetime


class InterviewKitSelectionUpdate(BaseModel):
    """One `included` flag per question, positionally aligned with the kit's existing
    `questions` order — the frontend already holds the full kit in memory, so a direct
    positional update avoids any risk of index drift between client and server."""

    included_flags: list[bool]
