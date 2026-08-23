from app.modules.interviews.llm_client import (
    AnthropicInterviewScorecardLLMClient,
    InterviewScorecardLLMClient,
)

_default_client: InterviewScorecardLLMClient | None = None


def get_interview_scorecard_llm_client() -> InterviewScorecardLLMClient:
    """Overridable via app.dependency_overrides — tests inject a FakeInterviewScorecardLLMClient
    instead of calling the real Claude API, same pattern as every other module's
    get_*_llm_client().

    Constructed lazily (on first real call), not at module import time — see
    app/modules/intelligence/dependencies.py for the full reasoning (an eager module-level
    instance would crash every test's `from app.main import app` when ANTHROPIC_API_KEY is
    unset, which it always is in CI/tests).
    """

    global _default_client
    if _default_client is None:
        _default_client = AnthropicInterviewScorecardLLMClient()
    return _default_client
