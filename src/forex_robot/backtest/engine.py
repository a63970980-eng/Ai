from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from forex_robot.domain.models import Side


@dataclass(frozen=True)
class BacktestResult:
    trades: int
    wins: int
    losses: int
    net_pnl: float
    max_drawdown: float
    win_rate: float
    profit_factor: float


def run_backtest(candles: pd.DataFrame, signal_fn, spread: float = 0.0, slippage: float = 0.0, fee: float = 0.0) -> BacktestResult:
    pnl = []; equity = 0.0; peak = 0.0; max_dd = 0.0
    for i in range(len(candles) - 1):
        history = candles.iloc[:i+1]
        signal = signal_fn(history)
        if signal is None: continue
        nxt = float(candles.close.iloc[i+1])
        cost = spread + slippage + fee
        direction = 1 if signal.side is Side.BUY else -1
        result = direction * (nxt - signal.entry) - cost
        pnl.append(result); equity += result; peak=max(peak,equity); max_dd=max(max_dd, peak-equity)
    wins=sum(x>0 for x in pnl); losses=sum(x<=0 for x in pnl); gross_win=sum(x for x in pnl if x>0); gross_loss=-sum(x for x in pnl if x<0)
    return BacktestResult(len(pnl), wins, losses, sum(pnl), max_dd, wins/len(pnl) if pnl else 0.0, gross_win/gross_loss if gross_loss else float("inf"))
