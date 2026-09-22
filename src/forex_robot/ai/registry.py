from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Iterable


@dataclass(frozen=True)
class ModelProfile:
    provider: str
    model: str
    role: str
    base_weight: float
    enabled: bool = True


DEFAULT_PROFILES = (
    ModelProfile("openai", "gpt-5.6-luna", "reasoning_reviewer", 1.20),
    ModelProfile("gemini", "gemini-2.5-flash", "independent_reviewer", 1.00),
    ModelProfile("openrouter", "qwen/qwen3-32b", "quant_reviewer", 1.00),
    ModelProfile("openrouter", "deepseek/deepseek-r1", "reasoning_critic", 1.00),
    ModelProfile("openrouter", "mistralai/mistral-small", "fast_reviewer", 0.80),
    ModelProfile("local", "qwen3:8b", "local_quant", 0.75),
    ModelProfile("local", "deepseek-r1:8b", "local_critic", 0.75),
    ModelProfile("local", "mistral", "local_fast", 0.65),
)


class ModelRegistry:
    def __init__(self, profiles: Iterable[ModelProfile] = DEFAULT_PROFILES) -> None:
        self._profiles = {(p.provider, p.model): p for p in profiles}

    def profiles(self) -> list[ModelProfile]:
        return list(self._profiles.values())

    def weight(self, provider: str, model: str, observed_accuracy: float | None = None) -> float:
        profile = self._profiles.get((provider, model))
        if profile is None or not profile.enabled:
            return 0.0
        if observed_accuracy is None:
            return profile.base_weight
        # Smoothly reward measured accuracy without allowing one model to dominate.
        accuracy = max(0.0, min(1.0, observed_accuracy))
        multiplier = 0.70 + 0.60 / (1.0 + exp(-8.0 * (accuracy - 0.5)))
        return profile.base_weight * multiplier

    def configured(self, configured: Iterable[tuple[str, str]]) -> list[ModelProfile]:
        result = []
        for provider, model in configured:
            profile = self._profiles.get((provider, model))
            if profile is None:
                profile = ModelProfile(provider, model, "custom", 0.70)
            if profile.enabled:
                result.append(profile)
        return result
