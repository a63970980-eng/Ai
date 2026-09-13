from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from forex_robot.ai.engine import AIEngine
from forex_robot.domain.models import Signal
from forex_robot.regime.detector import Regime


@dataclass(frozen=True)
class AIProviderResult:
    score: float
    explanation: str
    provider: str
    model: str


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: float = 12.0) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _bounded(value: object, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


class OpenRouterPredictor:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def predict_score(self, signal: Signal, regime: Regime) -> float:
        prompt = (
            "You are a constrained forex signal-ranking model. Return ONLY JSON with keys "
            "score and explanation. score must be 0..1. Do not invent market data, do not "
            "override risk controls, and do not issue trade instructions. "
            f"Regime={regime.value}; signal={signal.model_dump()}"
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 160,
            "messages": [
                {"role": "system", "content": "Rank the supplied candidate only."},
                {"role": "user", "content": prompt},
            ],
        }
        data = _post_json("https://openrouter.ai/api/v1/chat/completions", payload, {"Authorization": f"Bearer {self.api_key}"})
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return _bounded(parsed.get("score"), signal.confidence)


class GeminiPredictor:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def predict_score(self, signal: Signal, regime: Regime) -> float:
        prompt = (
            "Return ONLY JSON: {\"score\": number, \"explanation\": string}. "
            "score must be 0..1. Rank only the supplied forex candidate. Never override risk. "
            f"Regime={regime.value}; signal={signal.model_dump()}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        data = _post_json(url, payload, {})
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(content)
        return _bounded(parsed.get("score"), signal.confidence)


def build_ai_engine() -> tuple[AIEngine, str]:
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if openrouter_key:
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        return AIEngine(OpenRouterPredictor(openrouter_key, model)), f"openrouter:{model}"
    if gemini_key:
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        return AIEngine(GeminiPredictor(gemini_key, model)), f"gemini:{model}"
    return AIEngine(), "deterministic-baseline"
