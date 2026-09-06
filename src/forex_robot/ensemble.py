from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from forex_robot.domain.models import Signal
from forex_robot.regime.detector import Regime, detect_regime


@dataclass(frozen=True)
class EnsembleResult:
    signal: Signal | None
    regime: Regime
    votes: int


class Ensemble:
    def __init__(self, strategies: list[Callable[[str, pd.DataFrame], Signal | None]]):
        self.strategies = strategies

    def generate(self, symbol: str, candles: pd.DataFrame) -> EnsembleResult:
        regime = detect_regime(candles)
        signals = [s for s in (fn(symbol, candles) for fn in self.strategies) if s]
        if not signals:
            return EnsembleResult(None, regime, 0)
        buys = [s for s in signals if s.side.value == "buy"]
        sells = [s for s in signals if s.side.value == "sell"]
        chosen = max((buys, sells), key=len)
        if len(chosen) < 2 and len(signals) > 1:
            return EnsembleResult(None, regime, len(signals))
        best = max(chosen, key=lambda s: s.confidence)
        return EnsembleResult(best.model_copy(update={"confidence": min(.99, best.confidence + .05*(len(chosen)-1))}), regime, len(chosen))
