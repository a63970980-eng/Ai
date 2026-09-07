from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from forex_robot.domain.models import Signal
from forex_robot.regime.detector import Regime


class Predictor(Protocol):
    def predict_score(self, signal: Signal, regime: Regime) -> float: ...


@dataclass(frozen=True)
class AISignal:
    signal: Signal | None
    model_score: float
    regime: Regime
    explanation: str = ""
    model_name: str = "deterministic-baseline"


class AIEngine:
    """Hybrid model boundary: models rank context; risk/execution remain authoritative."""

    def __init__(self, predictor: Predictor | None = None) -> None:
        self.predictor = predictor

    def score(self, signal: Signal | None, regime: Regime) -> AISignal:
        if signal is None:
            return AISignal(None, 0.0, regime, "no candidate signal")
        if self.predictor is not None:
            raw = float(self.predictor.predict_score(signal, regime))
            score = max(0.0, min(1.0, raw))
            return AISignal(signal.model_copy(update={"confidence": score}), score, regime, "external model ranking")
        adjustment = 0.05 if regime is Regime.TREND else (-0.10 if regime is Regime.HIGH_VOLATILITY else 0.0)
        score = max(0.0, min(1.0, signal.confidence + adjustment))
        explanation = "trend regime adjustment" if adjustment > 0 else "high-volatility penalty" if adjustment < 0 else "neutral regime adjustment"
        return AISignal(signal.model_copy(update={"confidence": score}), score, regime, explanation)
