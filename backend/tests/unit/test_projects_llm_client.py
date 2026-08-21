from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.projects.llm_client import (
    AnthropicProjectsLLMClient,
    LLMRequestError,
    _ROLE_FIELDS_TOOL,
)


def _make_client() -> AnthropicProjectsLLMClient:
    # Constructing AsyncAnthropic with an empty key is fine — it doesn't validate against the
    # network at construction time, and these tests never let it make a real request (the
    # underlying .messages.create is always mocked below).
    return AnthropicProjectsLLMClient()


def _fake_tool_response(input_data: dict) -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input=input_data)
    return SimpleNamespace(content=[tool_block])


async def test_extract_role_fields_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response(
            {
                "seniority": "Senior",
                "location": "Remote (UK)",
                "salary_min": 90000,
                "salary_max": 110000,
            }
        )
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.extract_role_fields(
        role_brief="Looking for a senior backend engineer, £90k-£110k, remote (UK).",
        title="Senior Backend Engineer",
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_ROLE_FIELDS_TOOL]
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": _ROLE_FIELDS_TOOL["name"]}
    content = call_kwargs["messages"][0]["content"]
    assert "Senior Backend Engineer" in content
    assert "£90k-£110k" in content

    assert result.seniority == "Senior"
    assert result.location == "Remote (UK)"
    assert result.salary_min == 90000
    assert result.salary_max == 110000


async def test_missing_tool_use_block_raises_llm_request_error() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.extract_role_fields(role_brief="some brief", title="Some Role")


async def test_fields_default_to_null_when_not_stated() -> None:
    # The contract: "leave a field null rather than guess." A vague role brief with no salary,
    # location, or seniority mentioned should come back with every field null, not a guess.
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response(
            {"seniority": None, "location": None, "salary_min": None, "salary_max": None}
        )
    )

    result = await client.extract_role_fields(role_brief="We're hiring.", title="A Role")

    assert result.seniority is None
    assert result.location is None
    assert result.salary_min is None
    assert result.salary_max is None


async def test_missing_fields_in_tool_response_default_to_null() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({})
    )

    result = await client.extract_role_fields(role_brief="some brief", title="Some Role")

    assert result.seniority is None
    assert result.location is None
    assert result.salary_min is None
    assert result.salary_max is None


async def test_malformed_salary_raises_llm_request_error() -> None:
    # Regression-style guard: if Claude returns a non-numeric string for an integer field, this
    # must fail loudly rather than silently coerce or crash uncaught.
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response(
            {"seniority": None, "location": None, "salary_min": "not-a-number", "salary_max": None}
        )
    )

    with pytest.raises(LLMRequestError):
        await client.extract_role_fields(role_brief="brief", title="Role")
