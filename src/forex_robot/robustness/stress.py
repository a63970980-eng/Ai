from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class StressResult:
    scenario: str
    net_pnl: float
    max_drawdown: float
    worst_trade: float
    losing_streak: int


def stress_returns(
    returns: list[float],
    spread_factor: float = 1.5,
    slippage_factor: float = 1.5,
    volatility_factor: float = 1.0,
    seed: int = 42,
) -> StressResult:
    """Deterministic stress model for execution costs and volatility.

    The function deliberately does not claim broker realism; it is a reproducible
    robustness screen over an existing return series.
    """
    if not returns:
        return StressResult("empty", 0.0, 0.0, 0.0, 0)
    factors = (spread_factor, slippage_factor, volatility_factor)
    if not all(math.isfinite(v) and v > 0 for v in factors):
        raise ValueError("stress factors must be finite and positive")
    arr = np.asarray(returns, dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError("returns must contain only finite values")
    # Seed is part of the API for reproducibility; the current stress transform
    # is deterministic and therefore does not need random draws.
    _ = int(seed)
    stressed = arr * volatility_factor
    cost = float(np.mean(np.abs(arr)) * 0.01 * (spread_factor + slippage_factor - 2.0))
    stressed = stressed - cost
    equity = np.cumsum(stressed)
    peak = np.maximum.accumulate(np.maximum(equity, 0.0))
    drawdown = peak - equity
    current_streak = max_streak = 0
    for value in stressed:
        if value < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return StressResult(
        "spread_slippage_volatility",
        float(equity[-1]),
        float(drawdown.max(initial=0.0)),
        float(stressed.min(initial=0.0)),
        max_streak,
    )


def validate_market_frame(candles: list[dict[str, float]]) -> dict[str, int | bool]:
    """Detect common data-feed corruption before strategy evaluation."""
    required = {"open", "high", "low", "close"}
    missing = 0
    invalid = 0
    duplicate = 0
    previous_key: object | None = None
    for candle in candles:
        if not required.issubset(candle):
            missing += 1
            continue
        values = [candle[key] for key in required]
        if not all(math.isfinite(float(value)) and float(value) > 0 for value in values):
            invalid += 1
        key = candle.get("timestamp")
        if key is not None and key == previous_key:
            duplicate += 1
        previous_key = key
    return {
        "healthy": not missing and not invalid and not duplicate,
        "missing_ohlc": missing,
        "invalid_ohlc": invalid,
        "duplicate_timestamps": duplicate,
    }


def connection_failure() -> dict[str, str]:
    return {
        "action": "halt_new_orders",
        "preserve": "open_position_state",
        "recovery": "reconcile broker before resume",
    }
