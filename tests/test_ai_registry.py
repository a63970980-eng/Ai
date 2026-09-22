from forex_robot.ai.registry import ModelRegistry


def test_registry_has_bounded_adaptive_weights():
    registry = ModelRegistry()
    assert registry.weight("openai", "gpt-5.6-luna") > 0
    assert registry.weight("unknown", "missing") == 0
    low = registry.weight("openai", "gpt-5.6-luna", 0.0)
    high = registry.weight("openai", "gpt-5.6-luna", 1.0)
    assert low > 0
    assert high > low
