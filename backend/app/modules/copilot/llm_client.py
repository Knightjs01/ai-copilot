from dataclasses import dataclass
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings


class LLMRequestError(Exception):
    """Infrastructure-level failure talking to the LLM provider — not an AppError itself (this
    module doesn't know about HTTP), the service layer wraps this into one."""


def _as_list(value: Any, *, field_name: str) -> list[Any]:
    # See hiring_blueprint/llm_client.py's _as_list for why this guard exists — Claude
    # occasionally returns a list-typed field as a single string instead of an array.
    if not isinstance(value, list):
        raise LLMRequestError(
            f"Expected Claude's {field_name!r} field to be a list, got {type(value).__name__}"
        )
    return value


@dataclass
class CopilotRouteDraft:
    action: str = "reply"
    query: str | None = None
    message: str | None = None


class CopilotLLMClient(Protocol):
    async def route(
        self, *, message: str, history: list[dict[str, str]], context_type: str
    ) -> CopilotRouteDraft: ...

    async def generate_interview_prep(self, *, job_facts: dict[str, Any]) -> list[str]: ...


# One tool per real action, plus `reply` for anything else — greetings, clarifying questions, or
# explaining what the co-pilot can do. `tool_choice={"type": "any"}` (see route() below) forces
# Claude to call exactly one of these six; there is no path where it responds with plain text.
_SEARCH_JOBS_TOOL: dict[str, Any] = {
    "name": "search_jobs",
    "description": (
        "Use when the candidate wants to search or browse job listings using natural language, "
        "e.g. 'find me remote senior roles' or 'anything in fintech'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The candidate's search intent, cleaned up into a plain search phrase.",
            },
        },
        "required": ["query"],
    },
}

_EXPLAIN_MATCH_TOOL: dict[str, Any] = {
    "name": "explain_match",
    "description": (
        "Use when the candidate asks how well they match, or why they match, the job they are "
        "currently viewing. Only usable when the candidate is currently viewing a specific job "
        "listing — if they aren't, prefer the reply tool and ask them to open a job first."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

_SUGGEST_IMPROVEMENTS_TOOL: dict[str, Any] = {
    "name": "suggest_improvements",
    "description": (
        "Use when the candidate asks how to improve their Phantom Passport, their summary, or "
        "their profile in general."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

_SUMMARIZE_APPLICATIONS_TOOL: dict[str, Any] = {
    "name": "summarize_applications",
    "description": (
        "Use when the candidate asks about the status of their application(s), e.g. 'how is my "
        "application going' or 'what's the status of my applications'."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

_INTERVIEW_PREP_TOOL: dict[str, Any] = {
    "name": "interview_prep",
    "description": (
        "Use when the candidate asks for help preparing for an interview. Only usable when the "
        "candidate is currently viewing a specific interview — if they aren't, prefer the reply "
        "tool and ask them to open an interview first."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

_REPLY_TOOL: dict[str, Any] = {
    "name": "reply",
    "description": (
        "Use for greetings, small talk, clarifying questions, or anything that doesn't clearly "
        "match one of the other actions. Also use this to explain what you can help with if the "
        "candidate's request is unclear."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "A short, friendly, conversational reply.",
            },
        },
        "required": ["message"],
    },
}

_ROUTE_TOOLS: list[dict[str, Any]] = [
    _SEARCH_JOBS_TOOL,
    _EXPLAIN_MATCH_TOOL,
    _SUGGEST_IMPROVEMENTS_TOOL,
    _SUMMARIZE_APPLICATIONS_TOOL,
    _INTERVIEW_PREP_TOOL,
    _REPLY_TOOL,
]

_CONTEXT_NOTES: dict[str, str] = {
    "job": "The candidate is currently viewing a specific job listing, so explain_match is available.",
    "application": "The candidate is currently viewing their application(s).",
    "interview": (
        "The candidate is currently viewing a specific upcoming interview, so interview_prep is "
        "available."
    ),
    "passport": "The candidate is currently viewing their Phantom Passport.",
    "none": "The candidate is not currently viewing anything specific.",
}

_INTERVIEW_PREP_QUESTIONS_TOOL: dict[str, Any] = {
    "name": "record_interview_prep_questions",
    "description": (
        "Generates a short list of preparation questions grounded only in the given job's real "
        "requirements and description — do not invent qualifications not present in the job "
        "posting."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "3-6 questions the candidate should prepare to answer or ask, grounded in "
                    "the job's real requirements/description."
                ),
            },
        },
        "required": ["questions"],
    },
}


class AnthropicCopilotLLMClient:
    """Real CopilotLLMClient implementation, backed by the Claude API. Kept independent of every
    other module's LLM client, per this codebase's convention of not sharing LLM plumbing across
    domains — even though route() calls into other modules' *services*, it never shares their
    LLM client instances (each is injected separately, see copilot/api.py)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def route(
        self, *, message: str, history: list[dict[str, str]], context_type: str
    ) -> CopilotRouteDraft:
        system = (
            "You are Phantom AI, a scoped assistant for Shadow job candidates. You can only "
            "take one of the actions given as tools — never answer outside of the reply tool. "
            f"{_CONTEXT_NOTES.get(context_type, _CONTEXT_NOTES['none'])}"
        )
        messages: list[dict[str, str]] = [*history, {"role": "user", "content": message}]
        try:
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=512,
                system=system,
                tools=_ROUTE_TOOLS,
                tool_choice={"type": "any"},
                messages=messages,
            )
        except anthropic.APIError as exc:
            raise LLMRequestError(f"Claude API request failed: {exc}") from exc

        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use_block is None:
            raise LLMRequestError("Claude did not return the expected structured tool call")

        try:
            data = tool_use_block.input
            return CopilotRouteDraft(
                action=str(tool_use_block.name),
                query=data.get("query"),
                message=data.get("message"),
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc

    async def generate_interview_prep(self, *, job_facts: dict[str, Any]) -> list[str]:
        try:
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=768,
                tools=[_INTERVIEW_PREP_QUESTIONS_TOOL],
                tool_choice={"type": "tool", "name": _INTERVIEW_PREP_QUESTIONS_TOOL["name"]},
                messages=[{"role": "user", "content": f"Job posting:\n{job_facts}"}],
            )
        except anthropic.APIError as exc:
            raise LLMRequestError(f"Claude API request failed: {exc}") from exc

        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use_block is None:
            raise LLMRequestError("Claude did not return the expected structured tool call")

        try:
            data = tool_use_block.input
            return [str(v) for v in _as_list(data.get("questions", []), field_name="questions")]
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc
