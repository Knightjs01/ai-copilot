from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings

_RATINGS = ["Strong", "Moderate", "Weak"]
_RECOMMENDATIONS = ["Strong Hire", "Hire", "No Hire", "Strong No Hire"]


class LLMRequestError(Exception):
    """Infrastructure-level failure talking to the LLM provider — the service layer wraps this
    into an InterviewScorecardGenerationError, same convention as every other LLM client here."""


def _as_list(value: Any, *, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise LLMRequestError(
            f"Expected Claude's {field_name!r} field to be a list, got {type(value).__name__}"
        )
    return value


@dataclass
class CompetencyScoreExtraction:
    competency: str = ""
    rating: str = ""
    evidence: str = ""


@dataclass
class InterviewScorecardExtraction:
    competency_scores: list[CompetencyScoreExtraction] = field(default_factory=list)
    overall_recommendation: str = ""
    summary: str = ""


class InterviewScorecardLLMClient(Protocol):
    async def generate_scorecard(
        self, *, notes: str, job_title: str, requirements: list[str] | None
    ) -> InterviewScorecardExtraction: ...


_SCORECARD_TOOL: dict[str, Any] = {
    "name": "record_interview_scorecard",
    "description": (
        "Records a structured interview scorecard derived from an interviewer's own typed "
        "notes about a candidate. Identify 3-6 real competencies the notes actually discuss "
        "and rate each — do not invent a competency with no evidence in the notes, and do not "
        "use a fixed/standard competency list; the competencies must come from what this "
        "interviewer actually wrote."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "competency_scores": {
                "type": "array",
                "minItems": 3,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "properties": {
                        "competency": {
                            "type": "string",
                            "description": "A specific competency or skill area the notes discuss.",
                        },
                        "rating": {"type": "string", "enum": _RATINGS},
                        "evidence": {
                            "type": "string",
                            "description": "The specific line of reasoning from the notes backing this rating.",
                        },
                    },
                    "required": ["competency", "rating", "evidence"],
                },
                "description": "Only include competencies the notes actually discuss.",
            },
            "overall_recommendation": {"type": "string", "enum": _RECOMMENDATIONS},
            "summary": {
                "type": "string",
                "description": "One-sentence summary of the interviewer's overall take.",
            },
        },
        "required": ["competency_scores", "overall_recommendation", "summary"],
    },
}


class AnthropicInterviewScorecardLLMClient:
    """Real InterviewScorecardLLMClient implementation, backed by the Claude API. Only ever
    called with already-redacted interviewer notes (the service layer redacts before this class
    ever sees the text) — this class has no knowledge of PII handling, same separation of
    concerns as every other LLM client in this codebase."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def generate_scorecard(
        self, *, notes: str, job_title: str, requirements: list[str] | None
    ) -> InterviewScorecardExtraction:
        requirements_line = (
            f"Hiring manager's top requirements for this role:\n{', '.join(requirements)}\n\n"
            if requirements
            else ""
        )
        prompt = (
            "Score this interviewer's own typed notes about a candidate they just interviewed "
            f"for the role of {job_title}.\n\n"
            f"{requirements_line}"
            f"Interviewer's notes:\n{notes}"
        )
        try:
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=2048,
                tools=[_SCORECARD_TOOL],
                tool_choice={"type": "tool", "name": _SCORECARD_TOOL["name"]},
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMRequestError(f"Claude API request failed: {exc}") from exc

        data = self._extract_tool_input(response)
        try:
            competency_scores = [
                CompetencyScoreExtraction(
                    competency=str(item.get("competency", "")),
                    rating=str(item.get("rating", "")),
                    evidence=str(item.get("evidence", "")),
                )
                for item in _as_list(
                    data.get("competency_scores", []), field_name="competency_scores"
                )
            ]
            return InterviewScorecardExtraction(
                competency_scores=competency_scores,
                overall_recommendation=str(data.get("overall_recommendation", "")),
                summary=str(data.get("summary", "")),
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc

    @staticmethod
    def _extract_tool_input(response: Any) -> dict[str, Any]:
        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use_block is None:
            raise LLMRequestError("Claude did not return the expected structured tool call")
        result: dict[str, Any] = tool_use_block.input
        return result
