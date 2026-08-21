from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.prescreen_assessment.llm_client import (
    _ASSESSMENT_TOOL,
    _HANDOFF_TOOL,
    AnthropicPrescreenAssessmentLLMClient,
    LLMRequestError,
)


def _make_client() -> AnthropicPrescreenAssessmentLLMClient:
    # Constructing AsyncAnthropic with an empty key is fine — it doesn't validate against the
    # network at construction time, and these tests never let it make a real request (the
    # underlying .messages.create is always mocked below).
    return AnthropicPrescreenAssessmentLLMClient()


def _fake_tool_response(input_data: dict) -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input=input_data)
    return SimpleNamespace(content=[tool_block])


async def test_generate_assessment_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response(
            {
                "fit_rating": "Strong Fit",
                "fit_summary": "Excellent match.",
                "strengths": ["Python depth"],
                "gaps": ["No fintech experience"],
                "suggested_questions": ["Tell me about your last project."],
                "areas_to_probe": ["Unclear tenure at last role."],
            }
        )
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.generate_assessment(
        role_summary="A senior backend role.",
        must_have_qualifications=["5+ years Python"],
        nice_to_have_qualifications=["GraphQL experience"],
        key_responsibilities=["Own the payments service"],
        evaluation_criteria=["Technical depth"],
        top_requirements=["Distributed systems experience"],
        candidate_skills=["Python", "Kubernetes"],
        candidate_experience_summary="Backend engineer with 6 years experience.",
        candidate_education=[{"institution": "Test U", "degree": "BSc", "field": "CS"}],
        candidate_industry="Fintech",
        candidate_years_experience=8,
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_ASSESSMENT_TOOL]
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": _ASSESSMENT_TOOL["name"]}
    content = call_kwargs["messages"][0]["content"]
    assert "Distributed systems experience" in content
    assert "Backend engineer with 6 years experience." in content
    assert "GraphQL experience" in content
    assert "Own the payments service" in content
    assert "Fintech" in content
    assert "Candidate years of experience: 8" in content

    assert result.fit_rating == "Strong Fit"
    assert result.fit_summary == "Excellent match."
    assert result.strengths == ["Python depth"]
    assert result.gaps == ["No fintech experience"]
    assert result.suggested_questions == ["Tell me about your last project."]
    assert result.areas_to_probe == ["Unclear tenure at last role."]


async def test_generate_assessment_missing_tool_use_block_raises() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="no tool call")])
    )

    with pytest.raises(LLMRequestError):
        await client.generate_assessment(
            role_summary="role",
            must_have_qualifications=[],
            nice_to_have_qualifications=[],
            key_responsibilities=[],
            evaluation_criteria=[],
            top_requirements=[],
            candidate_skills=[],
            candidate_experience_summary="",
            candidate_education=[],
            candidate_industry=None,
            candidate_years_experience=None,
        )


async def test_generate_handoff_recommendations_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(
        return_value=_fake_tool_response(
            {"handoff_recommendations": ["Dig into their tenure gap."]}
        )
    )
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.generate_handoff_recommendations(
        fit_summary="Excellent match.",
        gaps=["No fintech experience"],
        areas_to_probe=["Unclear tenure at last role."],
        prescreen_notes="Candidate explained the gap was a sabbatical.",
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_HANDOFF_TOOL]
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": _HANDOFF_TOOL["name"]}
    assert "Candidate explained the gap was a sabbatical." in call_kwargs["messages"][0]["content"]

    assert result == ["Dig into their tenure gap."]


async def test_generate_assessment_rejects_string_instead_of_list() -> None:
    # Regression test: observed in production, Claude occasionally returns a list-typed field
    # as an XML-tagged string (e.g. "<item>...</item>") instead of a JSON array despite the
    # forced tool-use schema declaring an array. Must fail loudly, not silently iterate
    # character-by-character.
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response(
            {
                "fit_rating": "Good Fit",
                "fit_summary": "Summary.",
                "strengths": "<item>Not a real list</item>",
                "gaps": [],
                "suggested_questions": [],
                "areas_to_probe": [],
            }
        )
    )

    with pytest.raises(LLMRequestError):
        await client.generate_assessment(
            role_summary="role",
            must_have_qualifications=[],
            nice_to_have_qualifications=[],
            key_responsibilities=[],
            evaluation_criteria=[],
            top_requirements=[],
            candidate_skills=[],
            candidate_experience_summary="",
            candidate_education=[],
            candidate_industry=None,
            candidate_years_experience=None,
        )


async def test_generate_handoff_recommendations_rejects_string_instead_of_list() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response(
            {"handoff_recommendations": "<item>Not a real list</item>"}
        )
    )

    with pytest.raises(LLMRequestError):
        await client.generate_handoff_recommendations(
            fit_summary="", gaps=[], areas_to_probe=[], prescreen_notes=""
        )


async def test_generate_handoff_recommendations_missing_fields_defaults_to_empty() -> None:
    client = _make_client()
    client._client.messages.create = AsyncMock(  # type: ignore[method-assign]
        return_value=_fake_tool_response({})
    )

    result = await client.generate_handoff_recommendations(
        fit_summary="", gaps=[], areas_to_probe=[], prescreen_notes=""
    )

    assert result == []
