from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Any

from forex_robot.ai.engine import AIEngine
from forex_robot.domain.models import Signal
from forex_robot.regime.detector import Regime


@dataclass(frozen=True)
class AIProviderResult:
    score: float
    explanation: str
    provider: str
    model: str


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float = 12.0) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("AI provider returned a non-object JSON response")
    return decoded


def _bounded(value: object, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    if isinstance(value, str):
        try:
            return max(0.0, min(1.0, float(value.strip())))
        except ValueError:
            return default
    return default


def _parse_model_json(content: object) -> dict[str, Any]:
    if not isinstance(content, str):
        raise ValueError("AI provider returned non-text model content")
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("AI provider did not return valid JSON") from None
        parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("AI provider JSON result is not an object")
    return parsed


def _extract_content(data: dict[str, Any], provider: str) -> str:
    try:
        if provider == "openrouter":
            choices = data["choices"]
            if not isinstance(choices, list) or not choices:
                raise ValueError("missing model choices")
            message = choices[0]["message"]
            content = message["content"]
        else:
            candidates = data["candidates"]
            if not isinstance(candidates, list) or not candidates:
                raise ValueError("missing model candidates")
            content = candidates[0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"malformed {provider} response") from exc
    if not isinstance(content, str):
        raise ValueError(f"malformed {provider} text response")
    return content


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
        data = _post_json(
            "https://openrouter.ai/api/v1/chat/completions",
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
        )
        parsed = _parse_model_json(_extract_content(data, "openrouter"))
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
        parsed = _parse_model_json(_extract_content(data, "gemini"))
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
