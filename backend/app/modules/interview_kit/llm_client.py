from dataclasses import dataclass, field
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
class InterviewKitQuestionDraft:
    question_text: str = ""
    follow_up_prompts: list[str] = field(default_factory=list)


@dataclass
class InterviewKitExtraction:
    questions: list[InterviewKitQuestionDraft] = field(default_factory=list)


class InterviewKitLLMClient(Protocol):
    async def generate_kit(
        self,
        *,
        role_summary: str,
        must_have_qualifications: list[str],
        evaluation_criteria: list[str],
    ) -> InterviewKitExtraction: ...


_INTERVIEW_KIT_TOOL: dict[str, Any] = {
    "name": "record_interview_kit",
    "description": (
        "Records a structured, bias-resistant interview question kit. You will be given an "
        "ordered list of grounding items (must-have qualifications, then evaluation criteria). "
        "Return exactly one question object per grounding item, in the exact same order — no "
        "more, no fewer. Each question must be answerable with concrete evidence from the "
        "candidate's own experience (behavioral/situational framing), not a yes/no or opinion "
        "question, so interviewers across a hiring team can compare candidates on the same "
        "grounded basis."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_text": {
                            "type": "string",
                            "description": (
                                "A single, concrete, evidence-seeking interview question for "
                                "this grounding item."
                            ),
                        },
                        "follow_up_prompts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "1-2 short follow-up prompts an interviewer can use to probe "
                                "deeper on this question."
                            ),
                        },
                    },
                    "required": ["question_text", "follow_up_prompts"],
                },
                "description": (
                    "One question object per grounding item, in the same order they were given."
                ),
            },
        },
        "required": ["questions"],
    },
}


class AnthropicInterviewKitLLMClient:
    """Real InterviewKitLLMClient implementation, backed by the Claude API. Kept independent of
    hiring_blueprint/prescreen_assessment's LLM clients — a different domain (interview
    questions, not requirements or fit-scoring) with its own tool schema, following this
    codebase's convention of not sharing LLM plumbing across domains."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def generate_kit(
        self,
        *,
        role_summary: str,
        must_have_qualifications: list[str],
        evaluation_criteria: list[str],
    ) -> InterviewKitExtraction:
        grounding_items = list(must_have_qualifications) + list(evaluation_criteria)
        numbered_items = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(grounding_items))
        try:
            # See app/modules/intelligence/llm_client.py for why this needs type: ignore under
            # strict mypy — same runtime-constructed-dict-vs-TypedDict mismatch.
            response = await self._client.messages.create(  # type: ignore[call-overload]
                model=self._model,
                max_tokens=4096,
                tools=[_INTERVIEW_KIT_TOOL],
                tool_choice={"type": "tool", "name": _INTERVIEW_KIT_TOOL["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Build a structured interview question kit for the following role.\n\n"
                            f"Role summary: {role_summary}\n\n"
                            f"Grounding items ({len(grounding_items)} total, in order):\n"
                            f"{numbered_items}"
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
            raw_questions = _as_list(data.get("questions", []), field_name="questions")
            questions = [
                InterviewKitQuestionDraft(
                    question_text=str(item.get("question_text", "")),
                    follow_up_prompts=[
                        str(v)
                        for v in _as_list(
                            item.get("follow_up_prompts", []), field_name="follow_up_prompts"
                        )
                    ],
                )
                for item in raw_questions
            ]
        except (KeyError, TypeError, AttributeError) as exc:
            raise LLMRequestError(f"Malformed structured response from Claude: {exc}") from exc

        if len(questions) != len(grounding_items):
            raise LLMRequestError(
                f"Expected {len(grounding_items)} questions (one per grounding item), "
                f"got {len(questions)}"
            )

        return InterviewKitExtraction(questions=questions)
