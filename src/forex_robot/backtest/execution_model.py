from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutionModel:
    spread: float = 0.0
    slippage: float = 0.0
    commission: float = 0.0
    delay_bars: int = 0

    def entry_price(self, mid: float, side: str) -> float:
        direction = 1.0 if side.lower() == "buy" else -1.0
        return float(mid) + direction * (self.spread / 2.0 + self.slippage)

    def round_trip_cost(self, units: float) -> float:
        return abs(float(units)) * self.commission
