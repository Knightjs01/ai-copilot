from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.hiring_blueprint.llm_client import (
    AnthropicHiringBlueprintLLMClient,
    LLMRequestError,
    _BLUEPRINT_TOOL,
)


def _make_client() -> AnthropicHiringBlueprintLLMClient:
    # Constructing AsyncAnthropic with an empty key is fine — it doesn't validate against the
    # network at construction time, and these tests never let it make a real request (the
    # underlying .messages.create is always mocked below).
    return AnthropicHiringBlueprintLLMClient()


def _fake_tool_response(input_data: dict) -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input=input_data)
    return SimpleNamespace(content=[tool_block])


async def test_generate_blueprint_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response(
            {
                "role_summary": "A senior backend role.",
                "key_responsibilities": ["Build APIs", "Mentor engineers"],
                "must_have_qualifications": ["5+ years Python"],
                "nice_to_have_qualifications": ["Kubernetes"],
                "evaluation_criteria": ["Technical depth", "Communication"],
            }
        )
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.generate_blueprint(
        role_brief="Looking for a senior backend engineer to lead our platform team.",
        title="Senior Backend Engineer",
        department="Engineering",
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_BLUEPRINT_TOOL]
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": _BLUEPRINT_TOOL["name"]}
    content = call_kwargs["messages"][0]["content"]
    assert "Senior Backend Engineer" in content
    assert "Engineering" in content
    assert "Looking for a senior backend engineer to lead our platform team." in content

    assert result.role_summary == "A senior backend role."
    assert result.key_responsibilities == ["Build APIs", "Mentor engineers"]
    assert result.must_have_qualifications == ["5+ years Python"]
    assert result.nice_to_have_qualifications == ["Kubernetes"]
    assert result.evaluation_criteria == ["Technical depth", "Communication"]


async def test_missing_tool_use_block_raises_llm_request_error() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.generate_blueprint(role_brief="some brief", title="Some Role", department=None)


async def test_missing_fields_in_tool_response_default_to_empty() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({})
    )

    result = await client.generate_blueprint(
        role_brief="some brief", title="Some Role", department=None
    )

    assert result.role_summary == ""
    assert result.key_responsibilities == []
    assert result.must_have_qualifications == []
    assert result.nice_to_have_qualifications == []
    assert result.evaluation_criteria == []
