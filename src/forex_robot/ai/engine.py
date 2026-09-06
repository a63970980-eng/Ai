from __future__ import annotations

from dataclasses import dataclass
from forex_robot.domain.models import Signal
from forex_robot.regime.detector import Regime


@dataclass(frozen=True)
class AISignal:
    signal: Signal | None
    model_score: float
    regime: Regime


class AIEngine:
    """Model boundary. Production ML models can be plugged in without bypassing RiskGate."""
    def score(self, signal: Signal | None, regime: Regime) -> AISignal:
        if signal is None: return AISignal(None, 0.0, regime)
        adjustment = 0.05 if regime is Regime.TREND else (-0.10 if regime is Regime.HIGH_VOLATILITY else 0.0)
        score=max(0.0,min(1.0,signal.confidence+adjustment))
        return AISignal(signal.model_copy(update={"confidence":score}),score,regime)
