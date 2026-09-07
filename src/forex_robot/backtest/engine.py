from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

import pandas as pd

from forex_robot.backtest.execution_model import ExecutionModel
from forex_robot.domain.models import Side, Signal


@dataclass(frozen=True)
class BacktestTrade:
    entry_index: int
    exit_index: int
    side: str
    entry: float
    exit: float
    stop_loss: float
    take_profit: float
    pnl: float
    r_multiple: float
    exit_reason: str


@dataclass(frozen=True)
class BacktestResult:
    trades: int
    wins: int
    losses: int
    net_pnl: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    expectancy: float = 0.0
    avg_r: float = 0.0
    trade_log: tuple[BacktestTrade, ...] = ()


def _validate_costs(spread: float, slippage: float, fee: float, risk_per_trade: float, execution_delay: int) -> None:
    if spread < 0 or slippage < 0 or fee < 0:
        raise ValueError("spread, slippage, and fee cannot be negative")
    if not 0 < risk_per_trade <= 1:
        raise ValueError("risk_per_trade must be in (0, 1]")
    if execution_delay < 0:
        raise ValueError("execution_delay cannot be negative")


def run_backtest(
    candles: pd.DataFrame,
    signal_fn: Callable[[pd.DataFrame], Signal | None],
    spread: float = 0.0,
    slippage: float = 0.0,
    fee: float = 0.0,
    risk_per_trade: float = 1.0,
    execution_delay: int = 0,
) -> BacktestResult:
    _validate_costs(spread, slippage, fee, risk_per_trade, execution_delay)
    if candles.empty or len(candles) < 2:
        return BacktestResult(0, 0, 0, 0.0, 0.0, 0.0, math.inf)
    missing = {"open", "high", "low", "close"} - set(candles.columns)
    if missing:
        raise ValueError(f"missing OHLC columns: {sorted(missing)}")

    model = ExecutionModel(spread=spread, slippage=slippage, commission=fee, delay_bars=execution_delay)
    trades: list[BacktestTrade] = []
    i = 0
    while i < len(candles) - 1:
        signal = signal_fn(candles.iloc[: i + 1].copy())
        if signal is None:
            i += 1
            continue

        entry_i = i + execution_delay + 1
        if entry_i >= len(candles):
            break
        entry_mid = float(candles.close.iloc[entry_i])
        entry = model.entry_price(entry_mid, signal.side.value)
        sl = float(signal.stop_loss)
        tp = float(signal.take_profit)
        if signal.side is Side.BUY and not sl < entry < tp:
            raise ValueError("BUY signal must satisfy stop_loss < entry < take_profit")
        if signal.side is Side.SELL and not tp < entry < sl:
            raise ValueError("SELL signal must satisfy take_profit < entry < stop_loss")
        risk_distance = abs(entry - sl)

        j = entry_i
        exit_price = float(candles.close.iloc[-1])
        reason = "end_of_data"
        while j < len(candles):
            bar = candles.iloc[j]
            if signal.side is Side.BUY:
                hit_sl = float(bar.low) <= sl
                hit_tp = float(bar.high) >= tp
            else:
                hit_sl = float(bar.high) >= sl
                hit_tp = float(bar.low) <= tp
            if hit_sl and hit_tp:
                exit_price, reason = sl, "stop_loss_first"
                break
            if hit_sl:
                exit_price, reason = sl, "stop_loss"
                break
            if hit_tp:
                exit_price, reason = tp, "take_profit"
                break
            exit_price = float(bar.close)
            j += 1

        raw = exit_price - entry if signal.side is Side.BUY else entry - exit_price
        pnl_value = raw * risk_per_trade - abs(fee)
        trades.append(
            BacktestTrade(
                i, j, signal.side.value, entry, exit_price, sl, tp,
                pnl_value, pnl_value / risk_distance, reason,
            )
        )
        i = max(j + 1, i + 1)

    pnl_values = [trade.pnl for trade in trades]
    r_values = [trade.r_multiple for trade in trades]
    equity = peak = mdd = 0.0
    for value in pnl_values:
        equity += value
        peak = max(peak, equity)
        mdd = max(mdd, peak - equity)

    wins = sum(value > 0 for value in pnl_values)
    losses = sum(value < 0 for value in pnl_values)
    gross_wins = sum(value for value in pnl_values if value > 0)
    gross_losses = -sum(value for value in pnl_values if value < 0)
    count = len(pnl_values)
    return BacktestResult(
        count, wins, losses, sum(pnl_values), mdd,
        wins / count if count else 0.0,
        gross_wins / gross_losses if gross_losses else math.inf,
        sum(pnl_values) / count if count else 0.0,
        sum(r_values) / count if r_values else 0.0,
        tuple(trades),
    )
