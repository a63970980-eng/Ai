from __future__ import annotations

import math

import numpy as np


def monte_carlo(
    trade_returns: list[float],
    simulations: int = 5000,
    seed: int = 42,
    ruin_fraction: float = 0.5,
) -> dict[str, float]:
    if simulations <= 0:
        raise ValueError("simulations must be positive")
    if not 0 < ruin_fraction <= 1:
        raise ValueError("ruin_fraction must be in (0, 1]")
    if not trade_returns:
        return {
            "median_final": 0.0, "p05_final": 0.0, "p95_final": 0.0,
            "prob_loss": 0.0, "p95_drawdown": 0.0,
            "p95_losing_streak": 0.0, "risk_of_ruin": 0.0,
        }
    arr = np.asarray(trade_returns, dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError("trade_returns must contain only finite values")
    rng = np.random.default_rng(seed)
    paths = rng.choice(arr, (simulations, len(arr)), replace=True)
    finals = paths.sum(axis=1)
    dds: list[float] = []
    streaks: list[int] = []
    ruined = 0
    starting = float(np.sum(np.maximum(-arr, 0)) + 1.0)
    ruin_level = -starting * ruin_fraction
    for path in paths:
        equity = np.cumsum(path)
        peak = np.maximum.accumulate(np.maximum(equity, 0.0))
        dds.append(float((peak - equity).max(initial=0.0)))
        current = best = 0
        for value in path:
            current = current + 1 if value < 0 else 0
            best = max(best, current)
        streaks.append(best)
        ruined += int(float(equity.min(initial=0.0)) <= ruin_level)
    return {
        "median_final": float(np.median(finals)),
        "p05_final": float(np.quantile(finals, 0.05)),
        "p95_final": float(np.quantile(finals, 0.95)),
        "prob_loss": float(np.mean(finals < 0)),
        "p95_drawdown": float(np.quantile(dds, 0.95)),
        "p95_losing_streak": float(np.quantile(streaks, 0.95)),
        "risk_of_ruin": float(ruined / simulations),
    }
