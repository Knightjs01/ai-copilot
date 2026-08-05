from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.intelligence.llm_client import (
    AnthropicLLMClient,
    LLMRequestError,
    _EXTRACTION_TOOL,
)


def _make_client() -> AnthropicLLMClient:
    # Constructing AsyncAnthropic with an empty key is fine — it doesn't validate against the
    # network at construction time, and these tests never let it make a real request (the
    # underlying .messages.create is always mocked below).
    return AnthropicLLMClient()


def _fake_tool_response(input_data: dict) -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input=input_data)
    return SimpleNamespace(content=[tool_block])


async def test_extract_candidate_profile_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response(
            {
                "skills": ["Python", "SQL"],
                "experience_summary": "Backend engineer.",
                "education": [{"institution": "Test U", "degree": "BSc", "field": "CS"}],
                "narrative_summary": "A summary.",
            }
        )
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.extract_candidate_profile(redacted_text="[REDACTED_NAME] resume text")

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_EXTRACTION_TOOL]
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": _EXTRACTION_TOOL["name"]}
    assert "[REDACTED_NAME] resume text" in call_kwargs["messages"][0]["content"]

    assert result.skills == ["Python", "SQL"]
    assert result.experience_summary == "Backend engineer."
    assert result.education[0].institution == "Test U"
    assert result.narrative_summary == "A summary."


async def test_missing_tool_use_block_raises_llm_request_error() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.extract_candidate_profile(redacted_text="some text")


async def test_rejects_string_instead_of_list_for_skills() -> None:
    # Regression test: observed in production, Claude occasionally returns a list-typed field
    # as an XML-tagged string instead of a JSON array despite the forced tool-use schema
    # declaring an array. Must fail loudly, not silently iterate character-by-character.
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response(
            {
                "skills": "<item>Not a real list</item>",
                "experience_summary": "Backend engineer.",
                "education": [],
                "narrative_summary": "A summary.",
            }
        )
    )

    with pytest.raises(LLMRequestError):
        await client.extract_candidate_profile(redacted_text="some text")


async def test_missing_fields_in_tool_response_default_to_empty() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({})
    )

    result = await client.extract_candidate_profile(redacted_text="some text")

    assert result.skills == []
    assert result.experience_summary == ""
    assert result.education == []
    assert result.narrative_summary == ""
