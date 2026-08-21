from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings

_FIT_RATINGS = ["Strong Fit", "Good Fit", "Possible Fit", "Weak Fit"]


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
class AssessmentExtraction:
    fit_rating: str = ""
    fit_summary: str = ""
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    suggested_questions: list[str] = field(default_factory=list)
    areas_to_probe: list[str] = field(default_factory=list)


class PrescreenAssessmentLLMClient(Protocol):
    async def generate_assessment(
        self,
        *,
        role_summary: str,
        must_have_qualifications: list[str],
        nice_to_have_qualifications: list[str],
        key_responsibilities: list[str],
        evaluation_criteria: list[str],
        top_requirements: list[str],
        candidate_skills: list[str],
        candidate_experience_summary: str,
        candidate_education: list[dict[str, str]],
        candidate_industry: str | None,
        candidate_years_experience: int | None,
    ) -> AssessmentExtraction: ...

    async def generate_handoff_recommendations(
        self, *, fit_summary: str, gaps: list[str], areas_to_probe: list[str], prescreen_notes: str
    ) -> list[str]: ...


_ASSESSMENT_TOOL: dict[str, Any] = {
    "name": "record_prescreen_assessment",
    "description": (
        "Records a structured pre-screen fit assessment comparing a candidate's profile "
        "against a role's requirements, plus prep guidance for the pre-screen call."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "fit_rating": {
                "type": "string",
                "enum": _FIT_RATINGS,
                "description": "Overall fit rating against the role's requirements.",
            },
            "fit_summary": {
                "type": "string",
                "description": "A concise (2-4 sentence), neutral summary explaining the rating.",
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ways the candidate's profile matches the role's requirements.",
            },
            "gaps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ways the candidate's profile falls short of the requirements.",
            },
            "suggested_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Screening questions tailored to this candidate and role.",
            },
            "areas_to_probe": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Non-obvious areas worth digging into on the call that aren't clear just "
                    "from skimming the candidate's profile — ambiguities, unverified claims, "
                    "or gaps worth clarifying."
                ),
            },
        },
        "required": [
            "fit_rating",
            "fit_summary",
            "strengths",
            "gaps",
            "suggested_questions",
            "areas_to_probe",
        ],
    },
}

_HANDOFF_TOOL: dict[str, Any] = {
    "name": "record_handoff_recommendations",
    "description": (
        "Records recommendations for the hiring manager's next-round interview, informed by "
        "what actually happened on the pre-screen call — not just the candidate's CV."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "handoff_recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "What the next-round interviewer should dig into further, grounded in the "
                    "pre-screen call notes."
                ),
            },
        },
        "required": ["handoff_recommendations"],
    },
}


class AnthropicPrescreenAssessmentLLMClient:
    """Real PrescreenAssessmentLLMClient implementation, backed by the Claude API. Only ever
    called with already-redacted candidate data (the caller passes fields from the Phase 5
    IntelligencePack, never raw resume text) plus role-side data (blueprint/alignment) — this
    class has no knowledge of PII handling, same separation of concerns as the other LLM
    clients in this codebase."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def generate_assessment(
        self,
        *,
        role_summary: str,
        must_have_qualifications: list[str],
        nice_to_have_qualifications: list[str],
        key_responsibilities: list[str],
        evaluation_criteria: list[str],
        top_requirements: list[str],
        candidate_skills: list[str],
        candidate_experience_summary: str,
        candidate_education: list[dict[str, str]],
        candidate_industry: str | None,
        candidate_years_experience: int | None,
    ) -> AssessmentExtraction:
        education_lines = "\n".join(
            f"- {e.get('degree', '')} in {e.get('field', '')}, {e.get('institution', '')}"
            for e in candidate_education
        )
        prompt = (
            "Assess this candidate's fit for the role below, and suggest how to run a "
            "productive pre-screen call with them.\n\n"
            f"Role summary:\n{role_summary}\n\n"
            f"Key responsibilities:\n{', '.join(key_responsibilities)}\n\n"
            f"Must-have qualifications:\n{', '.join(must_have_qualifications)}\n\n"
            f"Nice-to-have qualifications:\n{', '.join(nice_to_have_qualifications)}\n\n"
            f"Evaluation criteria:\n{', '.join(evaluation_criteria)}\n\n"
            f"Hiring manager's top requirements:\n{', '.join(top_requirements)}\n\n"
            f"Candidate skills:\n{', '.join(candidate_skills)}\n\n"
            f"Candidate experience summary:\n{candidate_experience_summary}\n\n"
            f"Candidate education:\n{education_lines}\n\n"
            f"Candidate industry background: {candidate_industry or 'not specified'}\n"
            "Candidate years of experience: "
            f"{candidate_years_experience if candidate_years_experience is not None else 'not specified'}"
        )
        try:
            # See app/modules/intelligence/llm_client.py for why this needs type: ignore under
            # strict mypy — same runtime-constructed-dict-vs-TypedDict mismatch.
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=2048,
                tools=[_ASSESSMENT_TOOL],
                tool_choice={"type": "tool", "name": _ASSESSMENT_TOOL["name"]},
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMRequestError(f"Claude API request failed: {exc}") from exc

        data = self._extract_tool_input(response)
        try:
            return AssessmentExtraction(
                fit_rating=str(data.get("fit_rating", "")),
                fit_summary=str(data.get("fit_summary", "")),
                strengths=[
                    str(v) for v in _as_list(data.get("strengths", []), field_name="strengths")
                ],
                gaps=[str(v) for v in _as_list(data.get("gaps", []), field_name="gaps")],
                suggested_questions=[
                    str(v)
                    for v in _as_list(
                        data.get("suggested_questions", []), field_name="suggested_questions"
                    )
                ],
                areas_to_probe=[
                    str(v)
                    for v in _as_list(data.get("areas_to_probe", []), field_name="areas_to_probe")
                ],
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc

    async def generate_handoff_recommendations(
        self, *, fit_summary: str, gaps: list[str], areas_to_probe: list[str], prescreen_notes: str
    ) -> list[str]:
        prompt = (
            "Based on the original pre-screen fit assessment and the notes from the pre-screen "
            "call that actually took place, recommend what the hiring manager should dig into "
            "further in the next round. Ground your recommendations in the call notes, not just "
            "the original assessment.\n\n"
            f"Original fit summary:\n{fit_summary}\n\n"
            f"Original gaps identified:\n{', '.join(gaps)}\n\n"
            f"Original areas to probe (pre-call, from the CV alone):\n{', '.join(areas_to_probe)}\n\n"
            f"Pre-screen call notes:\n{prescreen_notes}"
        )
        try:
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=1024,
                tools=[_HANDOFF_TOOL],
                tool_choice={"type": "tool", "name": _HANDOFF_TOOL["name"]},
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMRequestError(f"Claude API request failed: {exc}") from exc

        data = self._extract_tool_input(response)
        try:
            return [
                str(v)
                for v in _as_list(
                    data.get("handoff_recommendations", []), field_name="handoff_recommendations"
                )
            ]
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
