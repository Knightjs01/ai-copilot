from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

import anthropic
from anthropic import AsyncAnthropic

from app.core.config import get_settings


class LLMRequestError(Exception):
    """Infrastructure-level failure talking to the LLM provider — not an AppError itself, the
    service layer wraps this into one. Same split as every other llm_client in this codebase."""


def _as_list(value: Any, *, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise LLMRequestError(
            f"Expected Claude's {field_name!r} field to be a list, got {type(value).__name__}"
        )
    return value


def _parse_date(value: Any) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value if len(value) == 10 else f"{value}-01-01")
    except ValueError:
        return None


@dataclass
class CareerEntryExtraction:
    title: str = ""
    company_name: str = ""
    company_name_anonymized: str = ""
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    responsibilities: str = ""
    achievements: list[str] = field(default_factory=list)


@dataclass
class PassportExtraction:
    headline: str = ""
    seniority: str = ""
    years_experience: int | None = None
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    career_entries: list[CareerEntryExtraction] = field(default_factory=list)


class LLMClient(Protocol):
    async def extract_passport_from_cv(self, *, redacted_text: str) -> PassportExtraction: ...

    async def suggest_summary_improvement(
        self, *, headline: str | None, summary: str, skills: list[str]
    ) -> str: ...

    async def suggest_skills(
        self, *, headline: str | None, summary: str | None, existing_skills: list[str]
    ) -> list[str]: ...

    async def suggest_industries(
        self, *, headline: str | None, summary: str | None, existing_industries: list[str]
    ) -> list[str]: ...


_EXTRACTION_TOOL: dict[str, Any] = {
    "name": "record_phantom_passport",
    "description": (
        "Records a structured professional profile extracted from a candidate's CV, for their "
        "own Phantom Passport (an anonymous professional profile — never shown alongside a "
        "name). For every career entry, also produce a generalized company descriptor that "
        "would not let a reader identify the specific employer — e.g. 'Stripe' becomes "
        "'Global Payments Platform', 'Google' becomes 'Global Technology Company'. Only use "
        "facts explicitly present in the text — never infer or invent experience, skills, or "
        "achievements not stated."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "headline": {
                "type": "string",
                "description": "A short professional headline, e.g. 'Senior Product Leader'.",
            },
            "seniority": {
                "type": "string",
                "description": "Seniority level implied by the CV, e.g. 'Senior', 'VP', 'Director'.",
            },
            "years_experience": {
                "type": "integer",
                "description": "Approximate total years of professional experience.",
            },
            "summary": {
                "type": "string",
                "description": "A neutral 2-3 sentence professional summary, no PII.",
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Technical and professional skills explicitly mentioned.",
            },
            "industries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Industries/sectors the candidate has worked in, e.g. 'FinTech'.",
            },
            "career_entries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "company_name": {
                            "type": "string",
                            "description": "The real employer name as written in the CV.",
                        },
                        "company_name_anonymized": {
                            "type": "string",
                            "description": "A generalized descriptor that doesn't identify the employer.",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "ISO date or year, e.g. '2021-01-01' or '2021'.",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "ISO date or year, omit or empty if current role.",
                        },
                        "is_current": {"type": "boolean"},
                        "responsibilities": {"type": "string"},
                        "achievements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific, measurable achievements stated in the CV.",
                        },
                    },
                    "required": ["title", "company_name", "company_name_anonymized"],
                },
            },
        },
        "required": ["headline", "seniority", "summary", "skills", "industries", "career_entries"],
    },
}


_SUMMARY_SUGGESTION_TOOL: dict[str, Any] = {
    "name": "record_summary_suggestion",
    "description": (
        "Records one improved rewrite of a candidate's professional summary — a suggestion "
        "only, never applied automatically. Keep the same facts (no inventing experience), "
        "tighten the language, and make it more specific and evidence-led."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "improved_summary": {
                "type": "string",
                "description": "A 2-3 sentence improved rewrite of the candidate's summary.",
            },
        },
        "required": ["improved_summary"],
    },
}

_SKILLS_SUGGESTION_TOOL: dict[str, Any] = {
    "name": "record_skill_suggestions",
    "description": (
        "Records a short list of skills a candidate may want to add to their profile, inferred "
        "from their headline and summary. Never repeat a skill already in existing_skills. Only "
        "suggest skills reasonably implied by the given text — never invent experience."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "suggested_skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 5 new skills not already present in existing_skills.",
            },
        },
        "required": ["suggested_skills"],
    },
}

_INDUSTRIES_SUGGESTION_TOOL: dict[str, Any] = {
    "name": "record_industry_suggestions",
    "description": (
        "Records a short list of industries/sectors a candidate may want to add to their "
        "profile, inferred from their headline and summary. Never repeat an industry already "
        "in existing_industries. Only suggest industries reasonably implied by the given text "
        "— never invent experience."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "suggested_industries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 5 new industries not already present in existing_industries.",
            },
        },
        "required": ["suggested_industries"],
    },
}


class AnthropicLLMClient:
    """Only ever called with already-redacted text — see phantom_passport/service.py, which
    redacts using the candidate's own known full_name (collected at candidate_auth signup)
    before this class ever sees the CV, exactly the same invariant intelligence/llm_client.py
    and prescreen_assessment/llm_client.py already enforce for company-side candidates."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def extract_passport_from_cv(self, *, redacted_text: str) -> PassportExtraction:
        try:
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
                            "anonymized CV text for the candidate's own Phantom Passport. Only "
                            "use facts present in the text.\n\nAnonymized CV:\n" + redacted_text
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
            career_entries = [
                CareerEntryExtraction(
                    title=str(entry.get("title", "")),
                    company_name=str(entry.get("company_name", "")),
                    company_name_anonymized=str(entry.get("company_name_anonymized", "")),
                    start_date=_parse_date(entry.get("start_date")),
                    end_date=_parse_date(entry.get("end_date")),
                    is_current=bool(entry.get("is_current", False)),
                    responsibilities=str(entry.get("responsibilities", "")),
                    achievements=[
                        str(a)
                        for a in _as_list(entry.get("achievements", []), field_name="achievements")
                    ],
                )
                for entry in _as_list(data.get("career_entries", []), field_name="career_entries")
            ]
            return PassportExtraction(
                headline=str(data.get("headline", "")),
                seniority=str(data.get("seniority", "")),
                years_experience=(
                    int(data["years_experience"])
                    if isinstance(data.get("years_experience"), (int, float))
                    else None
                ),
                summary=str(data.get("summary", "")),
                skills=[str(s) for s in _as_list(data.get("skills", []), field_name="skills")],
                industries=[
                    str(i) for i in _as_list(data.get("industries", []), field_name="industries")
                ],
                career_entries=career_entries,
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc

    async def suggest_summary_improvement(
        self, *, headline: str | None, summary: str, skills: list[str]
    ) -> str:
        headline_line = f"Headline: {headline}\n" if headline else ""
        skills_line = f"Skills: {', '.join(skills)}\n" if skills else ""
        try:
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=512,
                tools=[_SUMMARY_SUGGESTION_TOOL],
                tool_choice={"type": "tool", "name": _SUMMARY_SUGGESTION_TOOL["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Suggest one improved rewrite of this candidate's professional "
                            f"summary.\n\n{headline_line}{skills_line}Current summary:\n{summary}"
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
            return str(tool_use_block.input.get("improved_summary", ""))
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc

    async def suggest_skills(
        self, *, headline: str | None, summary: str | None, existing_skills: list[str]
    ) -> list[str]:
        headline_line = f"Headline: {headline}\n" if headline else ""
        summary_line = f"Summary: {summary}\n" if summary else ""
        existing_line = (
            f"Existing skills (do not repeat these): {', '.join(existing_skills)}\n"
            if existing_skills
            else ""
        )
        try:
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=512,
                tools=[_SKILLS_SUGGESTION_TOOL],
                tool_choice={"type": "tool", "name": _SKILLS_SUGGESTION_TOOL["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Suggest additional skills for this candidate's profile.\n\n"
                            f"{headline_line}{summary_line}{existing_line}"
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
            return [
                str(s)
                for s in _as_list(
                    tool_use_block.input.get("suggested_skills", []),
                    field_name="suggested_skills",
                )
            ]
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc

    async def suggest_industries(
        self, *, headline: str | None, summary: str | None, existing_industries: list[str]
    ) -> list[str]:
        headline_line = f"Headline: {headline}\n" if headline else ""
        summary_line = f"Summary: {summary}\n" if summary else ""
        existing_line = (
            f"Existing industries (do not repeat these): {', '.join(existing_industries)}\n"
            if existing_industries
            else ""
        )
        try:
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=512,
                tools=[_INDUSTRIES_SUGGESTION_TOOL],
                tool_choice={"type": "tool", "name": _INDUSTRIES_SUGGESTION_TOOL["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Suggest additional industries/sectors for this candidate's "
                            f"profile.\n\n{headline_line}{summary_line}{existing_line}"
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
            return [
                str(s)
                for s in _as_list(
                    tool_use_block.input.get("suggested_industries", []),
                    field_name="suggested_industries",
                )
            ]
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc
