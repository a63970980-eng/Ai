from __future__ import annotations
from dataclasses import dataclass
from forex_robot.domain.trading import AccountState
from forex_robot.domain.models import Signal

@dataclass(frozen=True)
class PortfolioRiskLimits:
    max_daily_loss_fraction: float = 0.02
    max_drawdown_fraction: float = 0.10
    max_open_positions: int = 3
    max_spread: float = 0.00020
    max_consecutive_losses: int = 3
    max_portfolio_risk: float = 0.02
    max_currency_exposure: float = float("inf")
    min_signal_confidence: float = 0.65

@dataclass(frozen=True)
class PortfolioDecision:
    allowed: bool
    reason: str

def evaluate_portfolio(account: AccountState, signal: Signal, spread: float, max_spread: float | None = None, max_consecutive_losses: int | None = None, limits: PortfolioRiskLimits | None = None) -> PortfolioDecision:
    cfg = limits or PortfolioRiskLimits(max_spread=max_spread if max_spread is not None else 0.00020, max_consecutive_losses=max_consecutive_losses if max_consecutive_losses is not None else 3)
    if account.kill_switch: return PortfolioDecision(False, "kill_switch")
    if account.equity <= 0: return PortfolioDecision(False, "invalid_equity")
    if account.open_positions >= cfg.max_open_positions: return PortfolioDecision(False, "max_open_positions")
    if account.day_start_equity > 0 and 1 - account.equity / account.day_start_equity >= cfg.max_daily_loss_fraction: return PortfolioDecision(False, "daily_loss_limit")
    if account.peak_equity > 0 and 1 - account.equity / account.peak_equity >= cfg.max_drawdown_fraction: return PortfolioDecision(False, "drawdown_limit")
    if account.consecutive_losses >= cfg.max_consecutive_losses: return PortfolioDecision(False, "consecutive_loss_limit")
    if spread > cfg.max_spread: return PortfolioDecision(False, "spread_limit")
    if account.portfolio_risk >= cfg.max_portfolio_risk: return PortfolioDecision(False, "portfolio_risk_limit")
    if any(abs(v) > cfg.max_currency_exposure for v in account.currency_exposure.values()): return PortfolioDecision(False, "currency_exposure_limit")
    if signal.confidence < cfg.min_signal_confidence: return PortfolioDecision(False, "signal_confidence")
    return PortfolioDecision(True, "approved")
