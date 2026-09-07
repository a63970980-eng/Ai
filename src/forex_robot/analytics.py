from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np


def analytics(returns: Sequence[float], periods_per_year: int = 252) -> dict[str, float]:
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if not returns:
        return {
            "trades": 0.0, "win_rate": 0.0, "profit_factor": 0.0,
            "expectancy": 0.0, "sharpe": 0.0, "sortino": 0.0,
            "max_drawdown": 0.0, "recovery_factor": 0.0, "avg_r": 0.0,
            "avg_win": 0.0, "avg_loss": 0.0, "max_win_streak": 0.0,
            "max_loss_streak": 0.0,
        }
    x = np.asarray(returns, dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("returns must contain only finite values")

    wins, losses = x[x > 0], x[x < 0]
    equity = np.cumsum(x)
    peak = np.maximum.accumulate(np.maximum(equity, 0.0))
    drawdowns = peak - equity
    mdd = float(drawdowns.max(initial=0.0))
    sd = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    downside_values = np.minimum(x, 0.0)
    downside = float(np.sqrt(np.mean(downside_values**2)))
    gross_loss = float(-losses.sum())
    pf = float(wins.sum() / gross_loss) if gross_loss else math.inf

    win_streak = loss_streak = max_win = max_loss = 0
    for value in x:
        if value > 0:
            win_streak += 1
            loss_streak = 0
        elif value < 0:
            loss_streak += 1
            win_streak = 0
        else:
            win_streak = loss_streak = 0
        max_win = max(max_win, win_streak)
        max_loss = max(max_loss, loss_streak)

    total = float(x.sum())
    mean = float(x.mean())
    return {
        "trades": float(len(x)),
        "win_rate": float(np.mean(x > 0)),
        "profit_factor": pf,
        "expectancy": mean,
        "sharpe": mean / sd * math.sqrt(periods_per_year) if sd else 0.0,
        "sortino": mean / downside * math.sqrt(periods_per_year) if downside else 0.0,
        "max_drawdown": mdd,
        "recovery_factor": total / mdd if mdd else math.inf,
        "avg_r": mean,
        "avg_win": float(wins.mean()) if wins.size else 0.0,
        "avg_loss": float(losses.mean()) if losses.size else 0.0,
        "max_win_streak": float(max_win),
        "max_loss_streak": float(max_loss),
    }
