from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings


class LLMRequestError(Exception):
    """Infrastructure-level failure talking to the LLM provider — not an AppError itself (this
    module doesn't know about HTTP), the service layer wraps this into one."""


@dataclass
class EducationEntry:
    institution: str
    degree: str
    field: str


@dataclass
class CandidateProfileExtraction:
    skills: list[str] = field(default_factory=list)
    experience_summary: str = ""
    education: list[EducationEntry] = field(default_factory=list)
    narrative_summary: str = ""


class LLMClient(Protocol):
    async def extract_candidate_profile(
        self, *, redacted_text: str
    ) -> CandidateProfileExtraction: ...


_EXTRACTION_TOOL: dict[str, Any] = {
    "name": "record_candidate_profile",
    "description": (
        "Records a structured, objective professional profile extracted from an anonymized "
        "resume. Only include facts explicitly present in the text — do not infer, embellish, "
        "speculate, or add any score, rating, or opinion."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Technical and professional skills explicitly mentioned in the text.",
            },
            "experience_summary": {
                "type": "string",
                "description": (
                    "A neutral, factual summary of the candidate's work experience (roles, "
                    "responsibilities, approximate duration) as described in the text."
                ),
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "institution": {"type": "string"},
                        "degree": {"type": "string"},
                        "field": {"type": "string"},
                    },
                    "required": ["institution", "degree", "field"],
                },
            },
            "narrative_summary": {
                "type": "string",
                "description": (
                    "A brief (2-3 sentence), neutral overview of the candidate's professional "
                    "background. No judgment, no fit assessment, no scoring."
                ),
            },
        },
        "required": ["skills", "experience_summary", "education", "narrative_summary"],
    },
}


class AnthropicLLMClient:
    """Real LLMClient implementation, backed by the Claude API. Only ever called with
    already-redacted text (see app/modules/intelligence/service.py) — this class has no
    knowledge of PII handling, that responsibility lives entirely upstream in Phase 4's
    Privacy Gateway."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def extract_candidate_profile(self, *, redacted_text: str) -> CandidateProfileExtraction:
        try:
            # The SDK types `tools`/`tool_choice`/`messages` as specific TypedDicts; our
            # runtime-constructed dicts are correct (verified by tests/unit/test_llm_client.py
            # and the real-API smoke test) but don't structurally satisfy those TypedDicts under
            # strict mypy — same category as the slowapi handler mismatch in app/main.py.
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=2048,
                tools=[_EXTRACTION_TOOL],
                tool_choice={"type": "tool", "name": _EXTRACTION_TOOL["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Extract a structured professional profile from the following "
                            "anonymized resume text. Only use facts present in the text — do "
                            "not infer or speculate.\n\n" + redacted_text
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
            education = [
                EducationEntry(
                    institution=str(entry.get("institution", "")),
                    degree=str(entry.get("degree", "")),
                    field=str(entry.get("field", "")),
                )
                for entry in data.get("education", [])
            ]
            return CandidateProfileExtraction(
                skills=[str(skill) for skill in data.get("skills", [])],
                experience_summary=str(data.get("experience_summary", "")),
                education=education,
                narrative_summary=str(data.get("narrative_summary", "")),
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc
