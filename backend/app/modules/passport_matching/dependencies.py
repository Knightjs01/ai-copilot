from app.modules.passport_matching.llm_client import (
    AnthropicPassportMatchingLLMClient,
    PassportMatchingLLMClient,
)

_default_client: PassportMatchingLLMClient | None = None


def get_passport_matching_llm_client() -> PassportMatchingLLMClient:
    """Overridable via app.dependency_overrides — tests inject a FakePassportMatchingLLMClient
    instead of calling the real Claude API, same pattern as every other module's LLM-client
    dependency (see interview_kit/dependencies.py).

    Constructed lazily (on first real call), not at module import time — an eager module-level
    instance would crash every test's `from app.main import app` when ANTHROPIC_API_KEY is
    unset, which it always is in CI/tests.
    """

    global _default_client
    if _default_client is None:
        _default_client = AnthropicPassportMatchingLLMClient()
    return _default_client
