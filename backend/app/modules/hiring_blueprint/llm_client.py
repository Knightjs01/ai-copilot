from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings


class LLMRequestError(Exception):
    """Infrastructure-level failure talking to the LLM provider — not an AppError itself (this
    module doesn't know about HTTP), the service layer wraps this into one."""


@dataclass
class HiringBlueprintExtraction:
    role_summary: str = ""
    key_responsibilities: list[str] = field(default_factory=list)
    must_have_qualifications: list[str] = field(default_factory=list)
    nice_to_have_qualifications: list[str] = field(default_factory=list)
    evaluation_criteria: list[str] = field(default_factory=list)


class HiringBlueprintLLMClient(Protocol):
    async def generate_blueprint(
        self, *, role_brief: str, title: str, department: str | None
    ) -> HiringBlueprintExtraction: ...


_BLUEPRINT_TOOL: dict[str, Any] = {
    "name": "record_hiring_blueprint",
    "description": (
        "Records a structured hiring blueprint derived from a hiring manager's role "
        "description. Only include what is reasonably implied by the role title, department, "
        "and brief provided — no interview structure or candidate scoring, those are handled "
        "elsewhere."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "role_summary": {
                "type": "string",
                "description": "A concise (2-3 sentence) summary of the role.",
            },
            "key_responsibilities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The main responsibilities of the role.",
            },
            "must_have_qualifications": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Qualifications, skills, or experience the role requires.",
            },
            "nice_to_have_qualifications": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Qualifications, skills, or experience that are a plus but not required.",
            },
            "evaluation_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Categories a hiring team should evaluate candidates against for this role "
                    "(e.g. 'Technical depth', 'Communication'). These seed future scorecards — "
                    "keep them as evaluation categories, not yes/no requirements."
                ),
            },
        },
        "required": [
            "role_summary",
            "key_responsibilities",
            "must_have_qualifications",
            "nice_to_have_qualifications",
            "evaluation_criteria",
        ],
    },
}


class AnthropicHiringBlueprintLLMClient:
    """Real HiringBlueprintLLMClient implementation, backed by the Claude API. Kept independent
    of app.modules.intelligence.llm_client — a different domain (role, not candidate) with its
    own tool schema, so the two modules don't share LLM plumbing."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def generate_blueprint(
        self, *, role_brief: str, title: str, department: str | None
    ) -> HiringBlueprintExtraction:
        department_line = f"Department: {department}\n" if department else ""
        try:
            # See app/modules/intelligence/llm_client.py for why this needs type: ignore under
            # strict mypy — same runtime-constructed-dict-vs-TypedDict mismatch.
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=2048,
                tools=[_BLUEPRINT_TOOL],
                tool_choice={"type": "tool", "name": _BLUEPRINT_TOOL["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Build a structured hiring blueprint for the following role.\n\n"
                            f"Title: {title}\n{department_line}Role brief:\n{role_brief}"
                        ),
                    }
                ],
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
            return HiringBlueprintExtraction(
                role_summary=str(data.get("role_summary", "")),
                key_responsibilities=[str(v) for v in data.get("key_responsibilities", [])],
                must_have_qualifications=[str(v) for v in data.get("must_have_qualifications", [])],
                nice_to_have_qualifications=[
                    str(v) for v in data.get("nice_to_have_qualifications", [])
                ],
                evaluation_criteria=[str(v) for v in data.get("evaluation_criteria", [])],
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc
