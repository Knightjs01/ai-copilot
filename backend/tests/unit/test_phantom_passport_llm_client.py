from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.phantom_passport.llm_client import (
    _EXTRACTION_TOOL,
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
