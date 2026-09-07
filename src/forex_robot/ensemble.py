from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from forex_robot.domain.models import Signal
from forex_robot.regime.detector import Regime, detect_regime


@dataclass(frozen=True)
class EnsembleResult:
    signal: Signal | None
    regime: Regime
    votes: int
    agreement: float = 0.0


class Ensemble:
    def __init__(
        self,
        strategies: list[Callable[[str, pd.DataFrame], Signal | None]],
        weights: list[float] | None = None,
    ) -> None:
        if weights is not None:
            if len(weights) != len(strategies):
                raise ValueError("weights must match strategies length")
            if any(weight < 0 for weight in weights):
                raise ValueError("strategy weights cannot be negative")
            if not any(weights):
                raise ValueError("at least one strategy weight must be positive")
        self.strategies = strategies
        self.weights = weights if weights is not None else [1.0] * len(strategies)

    def generate(self, symbol: str, candles: pd.DataFrame) -> EnsembleResult:
        regime = detect_regime(candles)
        outputs: list[tuple[Signal, float]] = []
        for index, strategy in enumerate(self.strategies):
            signal = strategy(symbol, candles)
            if signal is not None and signal.confidence >= 0:
                outputs.append((signal, self.weights[index]))

        if not outputs:
            return EnsembleResult(None, regime, 0, 0.0)

        buy_weight = sum(weight for signal, weight in outputs if signal.side.value == "buy")
        sell_weight = sum(weight for signal, weight in outputs if signal.side.value == "sell")
        total_weight = buy_weight + sell_weight
        chosen_side = "buy" if buy_weight > sell_weight else "sell"
        chosen_weight = max(buy_weight, sell_weight)
        agreement = chosen_weight / total_weight if total_weight else 0.0

        if len(outputs) > 1 and buy_weight == sell_weight:
            return EnsembleResult(None, regime, len(outputs), agreement)

        chosen = [
            (signal, weight)
            for signal, weight in outputs
            if signal.side.value == chosen_side
        ]
        best, _ = max(chosen, key=lambda item: item[0].confidence * item[1])
        confidence = min(0.99, best.confidence * (0.75 + 0.25 * agreement))
        return EnsembleResult(
            best.model_copy(update={"confidence": confidence}),
            regime,
            len(outputs),
            agreement,
        )
