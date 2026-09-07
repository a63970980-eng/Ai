from __future__ import annotations

from dataclasses import dataclass

from forex_robot.domain.models import Side


@dataclass(frozen=True)
class ExitPlan:
    stop_loss: float
    take_profits: tuple[float, ...]
    break_even_trigger_r: float = 1.0
    trail_atr: float = 1.5


def build_exit_plan(
    side: Side,
    entry: float,
    atr_value: float,
    risk_distance: float | None = None,
    tp_multiples: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0),
    atr_stop_multiple: float = 1.25,
) -> ExitPlan:
    if entry <= 0 or atr_value <= 0:
        raise ValueError("entry and ATR must be positive")
    if not tp_multiples or any(x <= 0 for x in tp_multiples):
        raise ValueError("TP multiples must be positive")
    distance = max(float(risk_distance or 0), float(atr_value) * atr_stop_multiple)
    if distance <= 0:
        raise ValueError("risk distance must be positive")
    if side is Side.BUY:
        sl = entry - distance
        tps = tuple(entry + m * distance for m in tp_multiples)
    else:
        sl = entry + distance
        tps = tuple(entry - m * distance for m in tp_multiples)
    return ExitPlan(sl, tps)


def break_even_stop(side: Side, entry: float, current_stop: float, trigger_price: float) -> float:
    if side is Side.BUY and trigger_price >= entry:
        return max(current_stop, entry)
    if side is Side.SELL and trigger_price <= entry:
        return min(current_stop, entry)
    return current_stop


def trailing_stop(
    side: Side,
    current: float,
    atr_value: float,
    multiplier: float = 1.5,
    existing: float | None = None,
) -> float:
    if atr_value <= 0 or multiplier <= 0:
        raise ValueError("ATR and trailing multiplier must be positive")
    candidate = current - float(atr_value) * multiplier if side is Side.BUY else current + float(atr_value) * multiplier
    if existing is None:
        return candidate
    return max(existing, candidate) if side is Side.BUY else min(existing, candidate)
