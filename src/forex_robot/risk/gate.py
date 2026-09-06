from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from forex_robot.domain.models import Signal
from forex_robot.domain.trading import RiskLimits


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str


class RiskGate:
    def __init__(self, limits: RiskLimits = RiskLimits()) -> None:
        self.limits = limits
        self.day_start: float | None = None
        self.peak: float | None = None
        self.killed = False
        self.day = date.today()

    def evaluate(
        self,
        equity: float,
        signal: Signal,
        open_positions: int,
        spread: float,
        portfolio_risk: float = 0.0,
        consecutive_losses: int = 0,
        news_blocked: bool = False,
    ) -> RiskDecision:
        if date.today() != self.day:
            self.day = date.today()
            self.day_start = equity
            self.peak = equity
            self.killed = False
        if self.killed:
            return RiskDecision(False, "kill_switch")
        if news_blocked:
            return RiskDecision(False, "news_block")
        if signal.confidence < 0.65:
            return RiskDecision(False, "confidence")
        if open_positions >= self.limits.max_open_positions:
            return RiskDecision(False, "max_open_positions")
        if spread > self.limits.max_spread:
            return RiskDecision(False, "spread")
        if portfolio_risk > self.limits.max_portfolio_risk:
            return RiskDecision(False, "portfolio_risk")
        if consecutive_losses >= self.limits.max_consecutive_losses:
            return RiskDecision(False, "consecutive_losses")

        if self.day_start is None:
            self.day_start = equity
        if self.peak is None:
            self.peak = equity
        else:
            self.peak = max(self.peak, equity)

        if equity <= self.day_start * (1 - self.limits.max_daily_loss_fraction):
            self.killed = True
            return RiskDecision(False, "daily_loss")
        if equity <= self.peak * (1 - self.limits.max_drawdown_fraction):
            self.killed = True
            return RiskDecision(False, "drawdown")
        return RiskDecision(True, "approved")

    def emergency_stop(self) -> None:
        self.killed = True

    def reset_kill(self) -> None:
        self.killed = False
