from app.modules.intelligence.llm_client import AnthropicLLMClient, LLMClient

_default_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Overridable via app.dependency_overrides — tests inject a FakeLLMClient instead of
    calling the real Claude API, same pattern as get_email_sender/get_file_storage.

    Constructed lazily (on first real call), not at module import time: with an override in
    place, FastAPI never calls this function at all, but the module still gets imported (via
    api.py -> main.py -> every test's `from app.main import app`) regardless of overrides. If
    AnthropicLLMClient() ever validates its API key at construction, an eager module-level
    instance would crash that import — and therefore every test in the suite, not just this
    module's — even when ANTHROPIC_API_KEY is unset, which it always is in CI/tests.
    """

    global _default_client
    if _default_client is None:
        _default_client = AnthropicLLMClient()
    return _default_client
