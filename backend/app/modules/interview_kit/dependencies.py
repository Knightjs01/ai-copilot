from app.modules.interview_kit.llm_client import (
    AnthropicInterviewKitLLMClient,
    InterviewKitLLMClient,
)

_default_client: InterviewKitLLMClient | None = None


def get_interview_kit_llm_client() -> InterviewKitLLMClient:
    """Overridable via app.dependency_overrides — tests inject a FakeInterviewKitLLMClient
    instead of calling the real Claude API, same pattern as hiring_blueprint's
    get_hiring_blueprint_llm_client.

    Constructed lazily (on first real call), not at module import time — an eager module-level
    instance would crash every test's `from app.main import app` when ANTHROPIC_API_KEY is
    unset, which it always is in CI/tests.
    """

    global _default_client
    if _default_client is None:
        _default_client = AnthropicInterviewKitLLMClient()
    return _default_client
