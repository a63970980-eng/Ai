from __future__ import annotations
from dataclasses import dataclass
from forex_robot.domain.trading import AccountState
from forex_robot.domain.models import Signal

@dataclass(frozen=True)
class PortfolioDecision:
    allowed:bool; reason:str

def evaluate_portfolio(account:AccountState, signal:Signal, spread:float, max_spread:float, max_consecutive_losses:int=3)->PortfolioDecision:
    if account.kill_switch: return PortfolioDecision(False,'kill_switch')
    if account.open_positions>=3: return PortfolioDecision(False,'max_open_positions')
    if account.day_start_equity and account.equity/account.day_start_equity<=.98: return PortfolioDecision(False,'daily_loss_limit')
    if account.peak_equity and account.equity/account.peak_equity<=.90: return PortfolioDecision(False,'drawdown_limit')
    if account.consecutive_losses>=max_consecutive_losses: return PortfolioDecision(False,'consecutive_loss_limit')
    if spread>max_spread: return PortfolioDecision(False,'spread_limit')
    if signal.confidence<.65: return PortfolioDecision(False,'signal_confidence')
    return PortfolioDecision(True,'approved')
