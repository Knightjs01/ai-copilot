from app.modules.copilot.llm_client import AnthropicCopilotLLMClient, CopilotLLMClient

_default_client: CopilotLLMClient | None = None


def get_copilot_llm_client() -> CopilotLLMClient:
    """Overridable via app.dependency_overrides — tests inject a FakeCopilotLLMClient instead of
    calling the real Claude API, same pattern as every other module's LLM-client dependency.

    Constructed lazily (on first real call), not at module import time — an eager module-level
    instance would crash every test's `from app.main import app` when ANTHROPIC_API_KEY is
    unset, which it always is in CI/tests.
    """
    global _default_client
    if _default_client is None:
        _default_client = AnthropicCopilotLLMClient()
    return _default_client
