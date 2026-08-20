import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.passport_matching.schemas import BoardFilters, PassportJobMatchRead

CopilotContextType = Literal["job", "application", "interview", "passport", "none"]

CopilotAction = Literal[
    "search_jobs",
    "explain_match",
    "suggest_improvements",
    "summarize_applications",
    "interview_prep",
    "reply",
]


class CopilotMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class CopilotChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context_type: CopilotContextType = "none"
    context_id: uuid.UUID | None = None
    history: list[CopilotMessage] = Field(default_factory=list, max_length=10)


class CopilotChatResponse(BaseModel):
    reply: str
    action: CopilotAction
    board_filters: BoardFilters | None = None
    match: PassportJobMatchRead | None = None
    suggested_summary: str | None = None
    interview_prep_questions: list[str] | None = None
