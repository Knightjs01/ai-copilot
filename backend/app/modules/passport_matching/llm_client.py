from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings

_MATCH_TIERS = ["Excellent Match", "Strong Match", "Potential Match", "Weak Match"]
_REMOTE_PREFERENCES = ["remote", "hybrid", "onsite", "flexible"]
_EMPLOYMENT_TYPES = ["full_time", "part_time", "contract", "fractional"]


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
class PassportMatchDraft:
    match_tier: str = "Weak Match"
    match_score: int = 0
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class BoardFilterDraft:
    seniority: str | None = None
    remote_preference: str | None = None
    employment_type: str | None = None
    location: str | None = None


class PassportMatchingLLMClient(Protocol):
    async def score_match(
        self, *, passport_snapshot: dict[str, Any], job_facts: dict[str, Any]
    ) -> PassportMatchDraft: ...

    async def parse_search_query(self, *, query: str) -> BoardFilterDraft: ...


_PASSPORT_MATCH_TOOL: dict[str, Any] = {
    "name": "record_passport_match",
    "description": (
        "Records how well a candidate's professional profile matches a specific job posting. "
        "Score honestly based only on the real fields given — do not invent qualifications the "
        "candidate didn't list, and do not penalize for information the job posting simply "
        "didn't provide. The tier is the primary signal a candidate sees; the numeric score is "
        "secondary and should be consistent with the tier (Excellent Match ~85-100, Strong Match "
        "~65-84, Potential Match ~40-64, Weak Match ~0-39)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "match_tier": {
                "type": "string",
                "enum": _MATCH_TIERS,
                "description": "The overall qualitative match tier.",
            },
            "match_score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "A 0-100 score consistent with match_tier.",
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "2-4 short, specific reasons the candidate fits this role.",
            },
            "gaps": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "0-4 short, specific gaps or mismatches — an empty list is fine for a "
                    "genuinely strong match."
                ),
            },
            "summary": {
                "type": "string",
                "description": "One or two sentences explaining the match in plain language.",
            },
        },
        "required": ["match_tier", "match_score", "strengths", "gaps", "summary"],
    },
}

_BOARD_FILTER_TOOL: dict[str, Any] = {
    "name": "record_board_filters",
    "description": (
        "Parses a candidate's free-text job search into structured filters for the real job "
        "board, which only supports exact-match filtering on these four fields. Only fill a "
        "field when the query clearly and specifically implies it — leave a field null rather "
        "than guessing, since a wrong guess (especially seniority or location, which have no "
        "fixed vocabulary) would silently return zero results instead of a broader, more "
        "helpful set."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "seniority": {
                "type": ["string", "null"],
                "description": (
                    "A specific seniority level literally implied by the query (e.g. 'Senior', "
                    "'Junior', 'Staff', 'Lead', 'Principal'), or null if not clearly stated."
                ),
            },
            "remote_preference": {
                "type": ["string", "null"],
                "enum": [*_REMOTE_PREFERENCES, None],
                "description": "One of the real remote-preference values, or null.",
            },
            "employment_type": {
                "type": ["string", "null"],
                "enum": [*_EMPLOYMENT_TYPES, None],
                "description": "One of the real employment-type values, or null.",
            },
            "location": {
                "type": ["string", "null"],
                "description": "A specific place name literally stated in the query, or null.",
            },
        },
        "required": ["seniority", "remote_preference", "employment_type", "location"],
    },
}


class AnthropicPassportMatchingLLMClient:
    """Real PassportMatchingLLMClient implementation, backed by the Claude API. Two related,
    forced-tool-call, one-shot methods on one client — mirrors phantom_passport/llm_client.py's
    own shape (suggest_summary_improvement + suggest_skills on one client), not split into two
    separate modules, since both concern finding/explaining job matches. Kept independent of
    every other module's LLM client, per this codebase's convention of not sharing LLM plumbing
    across domains."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def score_match(
        self, *, passport_snapshot: dict[str, Any], job_facts: dict[str, Any]
    ) -> PassportMatchDraft:
        try:
            # See app/modules/intelligence/llm_client.py for why this needs type: ignore under
            # strict mypy — same runtime-constructed-dict-vs-TypedDict mismatch.
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=1024,
                tools=[_PASSPORT_MATCH_TOOL],
                tool_choice={"type": "tool", "name": _PASSPORT_MATCH_TOOL["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Score how well this candidate profile matches this job posting.\n\n"
                            f"Candidate profile:\n{passport_snapshot}\n\n"
                            f"Job posting:\n{job_facts}"
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
            return PassportMatchDraft(
                match_tier=str(data["match_tier"]),
                match_score=int(data["match_score"]),
                strengths=[
                    str(v) for v in _as_list(data.get("strengths", []), field_name="strengths")
                ],
                gaps=[str(v) for v in _as_list(data.get("gaps", []), field_name="gaps")],
                summary=str(data.get("summary", "")),
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc

    async def parse_search_query(self, *, query: str) -> BoardFilterDraft:
        try:
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=512,
                tools=[_BOARD_FILTER_TOOL],
                tool_choice={"type": "tool", "name": _BOARD_FILTER_TOOL["name"]},
                messages=[{"role": "user", "content": f"Search query: {query}"}],
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
            return BoardFilterDraft(
                seniority=data.get("seniority") or None,
                remote_preference=data.get("remote_preference") or None,
                employment_type=data.get("employment_type") or None,
                location=data.get("location") or None,
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc
