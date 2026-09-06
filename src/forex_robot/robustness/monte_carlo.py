from __future__ import annotations

import numpy as np


def monte_carlo(trade_returns: list[float], simulations: int = 2000, seed: int = 42) -> dict[str, float]:
    if not trade_returns: return {"median_final": 0.0, "p05_final": 0.0, "p95_final": 0.0, "prob_loss": 0.0}
    rng=np.random.default_rng(seed); arr=np.asarray(trade_returns,float)
    paths=rng.choice(arr,(simulations,len(arr)),replace=True).sum(axis=1)
    return {"median_final":float(np.median(paths)),"p05_final":float(np.quantile(paths,.05)),"p95_final":float(np.quantile(paths,.95)),"prob_loss":float(np.mean(paths<0))}
