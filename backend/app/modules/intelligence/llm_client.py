from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings


class LLMRequestError(Exception):
    """Infrastructure-level failure talking to the LLM provider — not an AppError itself (this
    module doesn't know about HTTP), the service layer wraps this into one."""


def _as_list(value: Any, *, field_name: str) -> list[Any]:
    # Observed in production: despite the forced tool-use JSON schema declaring an array,
    # Claude occasionally returns a list-typed field as a single XML-tagged string instead
    # (e.g. "<item>...</item>\n<item>...</item>"). Iterating that directly would silently
    # produce one "entry" per character rather than per list item — fail loudly instead.
    if not isinstance(value, list):
        raise LLMRequestError(
            f"Expected Claude's {field_name!r} field to be a list, got {type(value).__name__}"
        )
    return value


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
    highlights: list[str] = field(default_factory=list)


class LLMClient(Protocol):
    async def extract_candidate_profile(
        self, *, redacted_text: str, hiring_manager_requirements: list[str]
    ) -> CandidateProfileExtraction: ...


_EXTRACTION_TOOL: dict[str, Any] = {
    "name": "record_candidate_profile",
    "description": (
        "Records a structured professional profile extracted from an anonymized resume, plus "
        "a short set of smart highlights comparing that profile against what the hiring "
        "manager said matters most for this role. skills/experience_summary/education/"
        "narrative_summary must stay strictly factual — only what's explicitly in the text, no "
        "score, rating, or opinion. highlights is the one evaluative field: specific, "
        "evidence-based observations connecting the candidate's actual background to the "
        "hiring manager's stated requirements — not a restatement of the CV."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Technical and professional skills explicitly mentioned in the text. List "
                    "the skills most relevant to the hiring manager's stated requirements "
                    "first, but only include skills actually present in the text — never add a "
                    "skill just because the hiring manager asked for it."
                ),
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
            "highlights": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "3-5 short, specific, evidence-based highlights connecting this candidate's "
                    "actual background to the hiring manager's stated requirements — e.g. '5 "
                    "years leading distributed systems teams directly matches the hiring "
                    "manager's #1 requirement'. Surface clear matches AND notable gaps against "
                    "the requirements. Every highlight must be grounded in specific evidence "
                    "from the resume text — never generic praise, never inferred beyond what's "
                    "written."
                ),
            },
        },
        "required": [
            "skills",
            "experience_summary",
            "education",
            "narrative_summary",
            "highlights",
        ],
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

    async def extract_candidate_profile(
        self, *, redacted_text: str, hiring_manager_requirements: list[str]
    ) -> CandidateProfileExtraction:
        requirements_block = "\n".join(f"- {r}" for r in hiring_manager_requirements)
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
                            "anonymized resume text, and write smart highlights comparing it "
                            "against what the hiring manager said matters most for this role. "
                            "Only use facts present in the resume text — do not infer or "
                            "speculate about the candidate.\n\n"
                            "Hiring manager's top requirements for this role:\n"
                            + requirements_block
                            + "\n\nAnonymized resume:\n"
                            + redacted_text
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
                for entry in _as_list(data.get("education", []), field_name="education")
            ]
            return CandidateProfileExtraction(
                skills=[
                    str(skill) for skill in _as_list(data.get("skills", []), field_name="skills")
                ],
                experience_summary=str(data.get("experience_summary", "")),
                education=education,
                narrative_summary=str(data.get("narrative_summary", "")),
                highlights=[
                    str(h) for h in _as_list(data.get("highlights", []), field_name="highlights")
                ],
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc
