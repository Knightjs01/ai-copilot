from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.interview_kit.llm_client import (
    AnthropicInterviewKitLLMClient,
    LLMRequestError,
    _INTERVIEW_KIT_TOOL,
)


def _make_client() -> AnthropicInterviewKitLLMClient:
    # Constructing AsyncAnthropic with an empty key is fine — it doesn't validate against the
    # network at construction time, and these tests never let it make a real request (the
    # underlying .messages.create is always mocked below).
    return AnthropicInterviewKitLLMClient()


def _fake_tool_response(input_data: dict) -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input=input_data)
    return SimpleNamespace(content=[tool_block])


async def test_generate_kit_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response(
            {
                "questions": [
                    {
                        "question_text": "Tell me about a time you used Python at scale.",
                        "follow_up_prompts": ["What was the hardest part?"],
                    },
                    {
                        "question_text": "Describe how you evaluated a candidate's depth.",
                        "follow_up_prompts": ["What evidence convinced you?"],
                    },
                ]
            }
        )
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.generate_kit(
        role_summary="A senior backend role.",
        must_have_qualifications=["5+ years Python"],
        evaluation_criteria=["Technical depth"],
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_INTERVIEW_KIT_TOOL]
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": _INTERVIEW_KIT_TOOL["name"]}
    content = call_kwargs["messages"][0]["content"]
    assert "A senior backend role." in content
    assert "5+ years Python" in content
    assert "Technical depth" in content

    assert len(result.questions) == 2
    assert result.questions[0].question_text == "Tell me about a time you used Python at scale."
    assert result.questions[0].follow_up_prompts == ["What was the hardest part?"]
    assert result.questions[1].question_text == "Describe how you evaluated a candidate's depth."


async def test_question_count_mismatch_raises_llm_request_error() -> None:
    # The core invariant this module adds over hiring_blueprint's pattern: one question per
    # grounding item, no more, no fewer. A short (or long) response must fail loudly rather than
    # silently misalign source_type/source_text zipping downstream in the service layer.
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response(
            {
                "questions": [
                    {"question_text": "Only one question.", "follow_up_prompts": []},
                ]
            }
        )
    )

    with pytest.raises(LLMRequestError):
        await client.generate_kit(
            role_summary="A role.",
            must_have_qualifications=["Skill A", "Skill B"],
            evaluation_criteria=["Criterion A"],
        )


async def test_missing_tool_use_block_raises_llm_request_error() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.generate_kit(
            role_summary="A role.", must_have_qualifications=["Skill A"], evaluation_criteria=[]
        )


async def test_rejects_string_instead_of_list_for_questions() -> None:
    # Regression guard mirroring hiring_blueprint's _as_list test: Claude occasionally returns
    # a list-typed field as an XML-tagged string instead of a JSON array.
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({"questions": "<item>Not a real list</item>"})
    )

    with pytest.raises(LLMRequestError):
        await client.generate_kit(
            role_summary="A role.", must_have_qualifications=["Skill A"], evaluation_criteria=[]
        )


async def test_empty_grounding_lists_produce_empty_questions() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({"questions": []})
    )

    result = await client.generate_kit(
        role_summary="A role.", must_have_qualifications=[], evaluation_criteria=[]
    )

    assert result.questions == []
