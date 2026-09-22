from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PositionSize:
    units: float
    risk_amount: float
    risk_distance: float


def calculate_position_size(
    equity: float,
    entry: float,
    stop_loss: float,
    risk_fraction: float,
    *,
    min_units: float = 0.0,
    max_units: float | None = None,
) -> PositionSize:
    values = (equity, entry, stop_loss, risk_fraction)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("position sizing inputs must be finite")
    if equity <= 0 or entry <= 0 or stop_loss <= 0:
        raise ValueError("equity, entry, and stop_loss must be positive")
    if not 0 < risk_fraction <= 0.05:
        raise ValueError("risk_fraction must be in (0, 0.05]")
    if min_units < 0 or (max_units is not None and max_units <= 0):
        raise ValueError("unit bounds are invalid")
    distance = abs(entry - stop_loss)
    if distance <= 0:
        raise ValueError("entry and stop_loss must differ")
    risk_amount = equity * risk_fraction
    units = risk_amount / distance
    if max_units is not None:
        units = min(units, max_units)
    units = max(units, min_units)
    if not math.isfinite(units) or units <= 0:
        raise ValueError("calculated position size is invalid")
    return PositionSize(units, risk_amount, distance)
