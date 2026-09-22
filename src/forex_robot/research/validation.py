from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class Window:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def walk_forward_windows(length: int, train_size: int, test_size: int, step: int | None = None) -> list[Window]:
    if min(length, train_size, test_size) <= 0:
        raise ValueError("length, train_size and test_size must be positive")
    step = test_size if step is None else step
    if step <= 0:
        raise ValueError("step must be positive")
    windows: list[Window] = []
    start = 0
    while start + train_size + test_size <= length:
        windows.append(Window(start, start + train_size, start + train_size, start + train_size + test_size))
        start += step
    return windows


@dataclass(frozen=True)
class MonteCarloSummary:
    simulations: int
    mean_total_return: float
    p05_total_return: float
    p50_total_return: float
    p95_total_return: float
    probability_of_loss: float
    worst_drawdown_p05: float


def monte_carlo_bootstrap(returns: Iterable[float], simulations: int = 2000, seed: int = 42) -> MonteCarloSummary:
    values = np.asarray(list(returns), dtype=float)
    if values.size < 2:
        raise ValueError("at least two returns are required")
    if simulations < 100:
        raise ValueError("simulations must be at least 100")
    if not np.isfinite(values).all():
        raise ValueError("returns must be finite")
    rng = random.Random(seed)
    totals: list[float] = []
    drawdowns: list[float] = []
    for _ in range(simulations):
        sample = [values[rng.randrange(values.size)] for _ in range(values.size)]
        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        for r in sample:
            equity *= 1.0 + float(r)
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak)
        totals.append(equity - 1.0)
        drawdowns.append(max_dd)
    q = np.percentile(totals, [5, 50, 95])
    return MonteCarloSummary(
        simulations=simulations,
        mean_total_return=float(np.mean(totals)),
        p05_total_return=float(q[0]),
        p50_total_return=float(q[1]),
        p95_total_return=float(q[2]),
        probability_of_loss=float(np.mean(np.asarray(totals) < 0)),
        worst_drawdown_p05=float(np.percentile(drawdowns, 95)),
    )
