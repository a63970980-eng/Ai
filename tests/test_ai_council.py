from forex_robot.ai.council import _model_specs


def test_council_without_configuration_is_safe(monkeypatch):
    for key in ("AI_COUNCIL_MODELS", "OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "LOCAL_AI_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    assert _model_specs() == []
