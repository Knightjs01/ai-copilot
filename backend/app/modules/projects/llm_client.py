from dataclasses import dataclass
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings


class LLMRequestError(Exception):
    """Infrastructure-level failure talking to the LLM provider — not an AppError itself (this
    module doesn't know about HTTP), the service layer wraps this into one."""


@dataclass
class RoleFieldsExtraction:
    seniority: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None


class ProjectsLLMClient(Protocol):
    async def extract_role_fields(self, *, role_brief: str, title: str) -> RoleFieldsExtraction: ...


_ROLE_FIELDS_TOOL: dict[str, Any] = {
    "name": "record_role_fields",
    "description": (
        "Extracts seniority, location, and salary range from a job description, if and only "
        "if explicitly stated or unambiguously implied. Leave a field null rather than guess "
        "— do not infer salary from seniority or location, and do not invent a location or "
        "seniority level not stated in the text."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "seniority": {
                "type": ["string", "null"],
                "description": "e.g. 'Senior', 'Staff', 'VP' — null if not stated.",
            },
            "location": {
                "type": ["string", "null"],
                "description": "e.g. 'Remote (UK)', 'London, UK' — null if not stated.",
            },
            "salary_min": {
                "type": ["integer", "null"],
                "description": "Lower bound of the stated salary range — null if no salary is mentioned.",
            },
            "salary_max": {
                "type": ["integer", "null"],
                "description": (
                    "Upper bound of the stated salary range — null if no salary is mentioned "
                    "or only one figure is given."
                ),
            },
        },
        "required": ["seniority", "location", "salary_min", "salary_max"],
    },
}


class AnthropicProjectsLLMClient:
    """Real ProjectsLLMClient implementation, backed by the Claude API. Kept independent of
    app.modules.hiring_blueprint.llm_client — this extracts and writes Project's own fields,
    hiring_blueprint only ever writes HiringBlueprint fields, so the two stay separate per this
    codebase's convention of not sharing LLM plumbing across domains."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def extract_role_fields(self, *, role_brief: str, title: str) -> RoleFieldsExtraction:
        try:
            # See app/modules/intelligence/llm_client.py for why this needs type: ignore under
            # strict mypy — same runtime-constructed-dict-vs-TypedDict mismatch.
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=512,
                tools=[_ROLE_FIELDS_TOOL],
                tool_choice={"type": "tool", "name": _ROLE_FIELDS_TOOL["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Extract seniority, location, and salary range from this job "
                            "description, if stated.\n\n"
                            f"Title: {title}\n\nRole brief:\n{role_brief}"
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
            raw_seniority = data.get("seniority")
            raw_location = data.get("location")
            raw_salary_min = data.get("salary_min")
            raw_salary_max = data.get("salary_max")
            return RoleFieldsExtraction(
                seniority=str(raw_seniority) if raw_seniority is not None else None,
                location=str(raw_location) if raw_location is not None else None,
                salary_min=int(raw_salary_min) if raw_salary_min is not None else None,
                salary_max=int(raw_salary_max) if raw_salary_max is not None else None,
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc
