import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.modules.interviews.llm_client import (
    AnthropicInterviewScorecardLLMClient,
    _SCORECARD_TOOL,
)


def _make_client() -> AnthropicInterviewScorecardLLMClient:
    # Constructing AsyncAnthropic with an empty key is fine — it doesn't validate against the
    # network at construction time, and these tests never let it make a real request (the
    # underlying .messages.create is always mocked below).
    return AnthropicInterviewScorecardLLMClient()


def _fake_tool_response(input_data: dict) -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input=input_data)
    return SimpleNamespace(content=[tool_block])


_WELL_FORMED_PAYLOAD = {
    "competency_scores": [
        {"competency": "Communication", "rating": "Strong", "evidence": "Clear and structured."}
    ],
    "overall_recommendation": "Hire",
    "summary": "A strong candidate overall.",
}


async def test_generate_scorecard_sends_forced_tool_use_request() -> None:
    client = _make_client()
    mock_create = AsyncMock(return_value=_fake_tool_response(_WELL_FORMED_PAYLOAD))
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.generate_scorecard(
        notes="Communicated clearly and gave strong examples.",
        job_title="Staff Product Designer",
        requirements=["Proven B2B SaaS track record"],
    )

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.await_args.kwargs
    assert call_kwargs["tools"] == [_SCORECARD_TOOL]
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": _SCORECARD_TOOL["name"]}
    content = call_kwargs["messages"][0]["content"]
    assert "Staff Product Designer" in content
    assert "Proven B2B SaaS track record" in content
    assert "Communicated clearly" in content

    assert len(result.competency_scores) == 1
    assert result.competency_scores[0].competency == "Communication"
    assert result.overall_recommendation == "Hire"
    assert result.summary == "A strong candidate overall."


async def test_generate_scorecard_recovers_from_double_encoded_payload() -> None:
    """Observed in production against this specific tool schema: Claude occasionally emits the
    entire tool payload as a JSON string under the first declared property instead of as real
    top-level fields. This must be recovered transparently, not surfaced as a 502."""

    client = _make_client()
    double_encoded = {"competency_scores": json.dumps(_WELL_FORMED_PAYLOAD)}
    mock_create = AsyncMock(return_value=_fake_tool_response(double_encoded))
    client._client.messages.create = mock_create  # type: ignore[method-assign]

    result = await client.generate_scorecard(
        notes="Some notes.", job_title="Staff Product Designer", requirements=None
    )

    assert len(result.competency_scores) == 1
    assert result.competency_scores[0].rating == "Strong"
    assert result.overall_recommendation == "Hire"
    assert result.summary == "A strong candidate overall."
