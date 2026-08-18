from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.phantom_passport.llm_client import (
    _EXTRACTION_TOOL,
    _INDUSTRIES_SUGGESTION_TOOL,
    _SKILLS_SUGGESTION_TOOL,
    _SUMMARY_SUGGESTION_TOOL,
    AnthropicLLMClient,
    LLMRequestError,
)


def _make_client() -> AnthropicLLMClient:
    return AnthropicLLMClient()


def _fake_tool_response(input_data: dict) -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input=input_data)
    return SimpleNamespace(content=[tool_block])


async def test_extract_passport_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response(
            {
                "headline": "Senior Product Leader",
                "seniority": "Senior",
                "years_experience": 12,
                "summary": "A summary.",
                "skills": ["Product Strategy"],
                "industries": ["FinTech"],
                "career_entries": [
                    {
                        "title": "VP Product",
                        "company_name": "Stripe",
                        "company_name_anonymized": "Global Payments Platform",
                        "start_date": "2021",
                        "is_current": True,
                        "responsibilities": "Led product strategy.",
                        "achievements": ["Scaled team 12 to 40"],
                    }
                ],
            }
        )
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.extract_passport_from_cv(redacted_text="[REDACTED_NAME] resume text")

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_EXTRACTION_TOOL]
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": _EXTRACTION_TOOL["name"]}
    assert "[REDACTED_NAME] resume text" in call_kwargs["messages"][0]["content"]

    assert result.headline == "Senior Product Leader"
    assert result.years_experience == 12
    assert result.skills == ["Product Strategy"]
    entry = result.career_entries[0]
    assert entry.company_name == "Stripe"
    assert entry.company_name_anonymized == "Global Payments Platform"
    assert entry.start_date is not None and entry.start_date.year == 2021
    assert entry.achievements == ["Scaled team 12 to 40"]


async def test_missing_tool_use_block_raises_llm_request_error() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.extract_passport_from_cv(redacted_text="some text")


async def test_rejects_string_instead_of_list_for_skills() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response(
            {
                "headline": "H",
                "seniority": "S",
                "summary": "Sum",
                "skills": "<item>Not a real list</item>",
                "industries": [],
                "career_entries": [],
            }
        )
    )

    with pytest.raises(LLMRequestError):
        await client.extract_passport_from_cv(redacted_text="some text")


async def test_missing_fields_in_tool_response_default_to_empty() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({})
    )

    result = await client.extract_passport_from_cv(redacted_text="some text")

    assert result.headline == ""
    assert result.years_experience is None
    assert result.skills == []
    assert result.career_entries == []


async def test_invalid_years_experience_type_falls_back_to_none() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response(
            {
                "headline": "H",
                "seniority": "S",
                "summary": "Sum",
                "skills": [],
                "industries": [],
                "career_entries": [],
                "years_experience": "not a number",
            }
        )
    )

    result = await client.extract_passport_from_cv(redacted_text="some text")

    assert result.years_experience is None


async def test_suggest_summary_improvement_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response({"improved_summary": "A tighter, more specific rewrite."})
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.suggest_summary_improvement(
        headline="Senior Product Leader", summary="Led things.", skills=["Product Strategy"]
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_SUMMARY_SUGGESTION_TOOL]
    assert call_kwargs["tool_choice"] == {
        "type": "tool",
        "name": _SUMMARY_SUGGESTION_TOOL["name"],
    }
    content = call_kwargs["messages"][0]["content"]
    assert "Senior Product Leader" in content
    assert "Led things." in content
    assert result == "A tighter, more specific rewrite."


async def test_suggest_summary_improvement_missing_tool_use_raises() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.suggest_summary_improvement(headline=None, summary="A summary.", skills=[])


async def test_suggest_skills_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response({"suggested_skills": ["Payments", "SaaS"]})
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.suggest_skills(
        headline="Senior Product Leader",
        summary="Led a payments platform.",
        existing_skills=["Leadership"],
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_SKILLS_SUGGESTION_TOOL]
    content = call_kwargs["messages"][0]["content"]
    assert "Leadership" in content
    assert result == ["Payments", "SaaS"]


async def test_suggest_skills_rejects_string_instead_of_list() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({"suggested_skills": "<item>Not a real list</item>"})
    )

    with pytest.raises(LLMRequestError):
        await client.suggest_skills(headline=None, summary=None, existing_skills=[])


async def test_suggest_skills_missing_tool_use_raises() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.suggest_skills(headline=None, summary=None, existing_skills=[])


async def test_suggest_industries_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response({"suggested_industries": ["FinTech", "B2B SaaS"]})
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.suggest_industries(
        headline="Senior Product Leader",
        summary="Led a payments platform.",
        existing_industries=["Payments"],
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_INDUSTRIES_SUGGESTION_TOOL]
    content = call_kwargs["messages"][0]["content"]
    assert "Payments" in content
    assert result == ["FinTech", "B2B SaaS"]


async def test_suggest_industries_rejects_string_instead_of_list() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({"suggested_industries": "<item>Not a real list</item>"})
    )

    with pytest.raises(LLMRequestError):
        await client.suggest_industries(headline=None, summary=None, existing_industries=[])


async def test_suggest_industries_missing_tool_use_raises() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.suggest_industries(headline=None, summary=None, existing_industries=[])
