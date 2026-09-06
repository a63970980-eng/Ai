from __future__ import annotations

from dataclasses import dataclass
from forex_robot.domain.models import Signal
from forex_robot.settings import settings


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str


class RiskGate:
    def __init__(self) -> None:
        self.day_start = None
        self.peak = None
        self.killed = False

    def evaluate(self, equity: float, signal: Signal, open_positions: int, spread: float) -> RiskDecision:
        if self.killed: return RiskDecision(False, "kill switch active")
        if signal.confidence < settings.min_signal_confidence: return RiskDecision(False, "confidence below threshold")
        if open_positions >= settings.max_open_positions: return RiskDecision(False, "maximum open positions reached")
        if spread > settings.max_spread_pips * 0.0001: return RiskDecision(False, "spread too wide")
        if self.day_start is None: self.day_start = equity
        self.peak = equity if self.peak is None else max(self.peak, equity)
        if equity <= self.day_start * (1-settings.max_daily_loss):
            self.killed = True; return RiskDecision(False, "daily loss limit reached")
        if equity <= self.peak * (1-settings.max_drawdown):
            self.killed = True; return RiskDecision(False, "maximum drawdown reached")
        return RiskDecision(True, "risk checks passed")

    def reset_kill(self) -> None:
        self.killed = False
