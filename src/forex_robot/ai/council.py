from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

from forex_robot.domain.models import Signal
from forex_robot.regime.detector import Regime
from forex_robot.ai.registry import ModelRegistry
from forex_robot.ai.ledger import ledger


@dataclass(frozen=True)
class ModelOpinion:
    provider: str
    model: str
    score: float
    confidence: float
    stance: str
    explanation: str
    latency_ms: float
    error: str | None = None


@dataclass(frozen=True)
class CouncilResult:
    opinions: list[ModelOpinion]
    consensus_score: float
    agreement: float
    stance: str
    conflicts: list[str]
    successful_models: int
    failed_models: int


def _bounded(value: Any, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _json_from_text(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("model did not return JSON")
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model JSON must be an object")
    return value


def _post(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider returned non-object JSON")
    return value


def _prompt(signal: Signal, regime: Regime, peer_context: str = "") -> str:
    return (
        "You are one member of a crypto quantitative research council. Analyze ONLY the supplied "
        "candidate signal. Do not invent prices, news, indicators, or market data. "
        "Do not place orders and never override deterministic risk controls. "
        "Return ONLY JSON with keys: score (0..1), confidence (0..1), stance "
        "(LONG|SHORT|WAIT), explanation (short string). "
        f"Regime={regime.value}; Signal={signal.model_dump(mode='json')}; "
        f"Peer opinions={peer_context or 'none'}"
    )


def _extract_openai(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    for item in data.get("output", []):
        for part in item.get("content", []):
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                return part["text"]
    raise ValueError("missing OpenAI response text")


def _extract_gemini(data: dict[str, Any]) -> str:
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("missing Gemini candidates")
    return candidates[0]["content"]["parts"][0]["text"]


def _extract_chat(data: dict[str, Any]) -> str:
    return data["choices"][0]["message"]["content"]


def _call(provider: str, model: str, signal: Signal, regime: Regime, peer_context: str) -> ModelOpinion:
    started = time.perf_counter()
    try:
        prompt = _prompt(signal, regime, peer_context)
        if provider == "openai":
            key = os.getenv("OPENAI_API_KEY", "").strip()
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not configured")
            data = _post(
                "https://api.openai.com/v1/responses",
                {"model": model, "input": prompt},
                {"Authorization": f"Bearer {key}"},
                20,
            )
            parsed = _json_from_text(_extract_openai(data))
        elif provider == "gemini":
            key = os.getenv("GEMINI_API_KEY", "").strip()
            if not key:
                raise RuntimeError("GEMINI_API_KEY is not configured")
            data = _post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                {"contents": [{"parts": [{"text": prompt}]}]},
                {},
                20,
            )
            parsed = _json_from_text(_extract_gemini(data))
        elif provider == "openrouter":
            key = os.getenv("OPENROUTER_API_KEY", "").strip()
            if not key:
                raise RuntimeError("OPENROUTER_API_KEY is not configured")
            data = _post(
                "https://openrouter.ai/api/v1/chat/completions",
                {
                    "model": model,
                    "temperature": 0,
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
                {"Authorization": f"Bearer {key}"},
                20,
            )
            parsed = _json_from_text(_extract_chat(data))
        elif provider == "local":
            base = os.getenv("LOCAL_AI_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
            data = _post(
                f"{base}/chat/completions",
                {
                    "model": model,
                    "temperature": 0,
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
                {},
                20,
            )
            parsed = _json_from_text(_extract_chat(data))
        else:
            raise RuntimeError(f"unsupported council provider: {provider}")

        score = _bounded(parsed.get("score"), signal.confidence)
        confidence = _bounded(parsed.get("confidence"), score)
        stance = str(parsed.get("stance", "WAIT")).upper()
        if stance not in {"LONG", "SHORT", "WAIT"}:
            stance = "WAIT"
        explanation = str(parsed.get("explanation", ""))[:1000]
        return ModelOpinion(
            provider, model, score, confidence, stance, explanation,
            (time.perf_counter() - started) * 1000,
        )
    except Exception as exc:
        return ModelOpinion(
            provider, model, 0.0, 0.0, "WAIT", "",
            (time.perf_counter() - started) * 1000, str(exc),
        )


def _model_specs() -> list[tuple[str, str]]:
    raw = os.getenv("AI_COUNCIL_MODELS", "").strip()
    if raw:
        specs: list[tuple[str, str]] = []
        for item in raw.split(","):
            if ":" not in item:
                continue
            provider, model = item.split(":", 1)
            if provider.strip() and model.strip():
                specs.append((provider.strip().lower(), model.strip()))
        return specs

    specs = []
    if os.getenv("OPENAI_API_KEY"):
        specs.append(("openai", os.getenv("OPENAI_MODEL", "gpt-5.6-luna")))
    if os.getenv("GEMINI_API_KEY"):
        specs.append(("gemini", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")))
    if os.getenv("OPENROUTER_API_KEY"):
        specs.extend([
            ("openrouter", "qwen/qwen3-32b"),
            ("openrouter", "deepseek/deepseek-r1"),
            ("openrouter", "mistralai/mistral-small"),
        ])
    if os.getenv("LOCAL_AI_BASE_URL"):
        specs.extend([
            ("local", "qwen3:8b"),
            ("local", "deepseek-r1:8b"),
            ("local", "mistral"),
        ])
    return specs


def run_council(signal: Signal, regime: Regime) -> CouncilResult:
    specs = _model_specs()
    if not specs:
        return CouncilResult([], signal.confidence, 0.0, "WAIT", ["no AI models configured"], 0, 0)

    first_pass = [_call(provider, model, signal, regime, "") for provider, model in specs]
    successful = [x for x in first_pass if x.error is None]

    peer_context = "; ".join(
        f"{x.provider}/{x.model}: {x.stance} score={x.score:.2f} conf={x.confidence:.2f}"
        for x in successful
    )
    opinions = [
        _call(provider, model, signal, regime, peer_context)
        for provider, model in specs
    ]
    valid = [x for x in opinions if x.error is None]
    if not valid:
        return CouncilResult(opinions, 0.0, 0.0, "WAIT", ["all models failed"], 0, len(opinions))

    registry = ModelRegistry()
    observed = {
        (row["provider"], row["model"]): row["accuracy"]
        for row in ledger.performance()
        if row.get("accuracy") is not None and row.get("settled", 0) >= 5
    }
    weights = [
        max(0.05, x.confidence)
        * registry.weight(x.provider, x.model, observed.get((x.provider, x.model)))
        for x in valid
    ]
    total_weight = sum(weights)
    consensus = sum(x.score * w for x, w in zip(valid, weights)) / total_weight
    stance_votes = {"LONG": 0.0, "SHORT": 0.0, "WAIT": 0.0}
    for x, w in zip(valid, weights):
        stance_votes[x.stance] += w
    stance = max(stance_votes.items(), key=lambda item: item[1])[0]
    agreement = max(stance_votes.values()) / total_weight

    conflicts: list[str] = []
    if stance_votes["LONG"] > 0 and stance_votes["SHORT"] > 0:
        conflicts.append("long_short_disagreement")
    if agreement < 0.60:
        conflicts.append("low_consensus")
    if len(valid) < len(opinions):
        conflicts.append("model_failures")

    return CouncilResult(
        opinions, consensus, agreement, stance, conflicts,
        len(valid), len(opinions) - len(valid),
    )
