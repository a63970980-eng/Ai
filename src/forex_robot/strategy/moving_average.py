from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from forex_robot.domain.models import Signal, Side


class MovingAverageStrategy:
    """Baseline strategy used as a deterministic benchmark for the AI layer."""

    def __init__(self, fast: int = 20, slow: int = 50) -> None:
        if fast <= 0 or slow <= fast:
            raise ValueError("slow must be greater than fast and both must be positive")
        self.fast = fast
        self.slow = slow

    def generate(self, symbol: str, candles: pd.DataFrame) -> Signal | None:
        if len(candles) < self.slow:
            return None
        close = candles["close"]
        fast_ma = close.rolling(self.fast).mean().iloc[-1]
        slow_ma = close.rolling(self.slow).mean().iloc[-1]
        price = float(close.iloc[-1])
        if pd.isna(fast_ma) or pd.isna(slow_ma):
            return None

        if fast_ma > slow_ma:
            side = Side.BUY
            stop = price * 0.995
            target = price * 1.01
            reason = "fast moving average is above slow moving average"
        elif fast_ma < slow_ma:
            side = Side.SELL
            stop = price * 1.005
            target = price * 0.99
            reason = "fast moving average is below slow moving average"
        else:
            return None

        confidence = min(0.95, 0.5 + abs(float(fast_ma - slow_ma)) / price * 10)
        return Signal(
            symbol=symbol,
            side=side,
            confidence=confidence,
            entry=price,
            stop_loss=stop,
            take_profit=target,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
        )
