from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

import pandas as pd

from forex_robot.backtest.execution_model import ExecutionModel
from forex_robot.backtest.exits import BacktestExitConfig
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
    units: float
    risk_amount: float
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
    if not all(math.isfinite(v) for v in (spread, slippage, fee, risk_per_trade)):
        raise ValueError("backtest costs and risk must be finite")
    if spread < 0 or slippage < 0 or fee < 0:
        raise ValueError("spread, slippage, and fee cannot be negative")
    if not 0 < risk_per_trade <= 1:
        raise ValueError("risk_per_trade must be in (0, 1]")
    if execution_delay < 0:
        raise ValueError("execution_delay cannot be negative")


def _atr(candles: pd.DataFrame, index: int, period: int = 14) -> float:
    start = max(0, index - period + 1)
    window = candles.iloc[start : index + 1]
    previous = window.close.shift(1).fillna(window.close)
    true_range = pd.concat(
        [window.high - window.low, (window.high - previous).abs(), (window.low - previous).abs()],
        axis=1,
    ).max(axis=1)
    value = float(true_range.mean())
    return value if math.isfinite(value) and value > 0 else 0.0


def run_backtest(
    candles: pd.DataFrame,
    signal_fn: Callable[[pd.DataFrame], Signal | None],
    spread: float = 0.0,
    slippage: float = 0.0,
    fee: float = 0.0,
    risk_per_trade: float = 1.0,
    execution_delay: int = 0,
    account_equity: float = 100_000.0,
    exit_config: BacktestExitConfig | None = None,
) -> BacktestResult:
    _validate_costs(spread, slippage, fee, risk_per_trade, execution_delay)
    if not math.isfinite(account_equity) or account_equity <= 0:
        raise ValueError("account_equity must be finite and positive")
    if candles.empty or len(candles) < 2:
        return BacktestResult(0, 0, 0, 0.0, 0.0, 0.0, math.inf)
    missing = {"open", "high", "low", "close"} - set(candles.columns)
    if missing:
        raise ValueError(f"missing OHLC columns: {sorted(missing)}")
    numeric = candles[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or (numeric <= 0).any().any():
        raise ValueError("OHLC data must be finite and positive")

    model = ExecutionModel(spread=spread, slippage=slippage, commission=fee, delay_bars=execution_delay)
    cfg = exit_config
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
        initial_sl = float(signal.stop_loss)
        initial_tp = float(signal.take_profit)
        if not all(math.isfinite(v) and v > 0 for v in (entry, initial_sl, initial_tp)):
            raise ValueError("signal prices must be finite and positive")
        if signal.side is Side.BUY and not initial_sl < entry < initial_tp:
            raise ValueError("BUY signal must satisfy stop_loss < entry < take_profit")
        if signal.side is Side.SELL and not initial_tp < entry < initial_sl:
            raise ValueError("SELL signal must satisfy take_profit < entry < stop_loss")
        risk_distance = abs(entry - initial_sl)
        risk_amount = account_equity * risk_per_trade
        units = risk_amount / risk_distance
        if not math.isfinite(units) or units <= 0:
            raise ValueError("calculated backtest position size is invalid")

        stop = initial_sl
        remaining = units
        realized = 0.0
        weighted_exit = 0.0
        exited_units = 0.0
        targets = tuple(entry + (1 if signal.side is Side.BUY else -1) * m * risk_distance
                        for m in (cfg.take_profit_multiples if cfg else ()))
        fractions = cfg.partial_exit_fractions if cfg else ()
        next_target = 0
        j = entry_i
        exit_price = float(candles.close.iloc[-1])
        reason = "end_of_data"
        while j < len(candles):
            bar = candles.iloc[j]
            if cfg:
                current_atr = _atr(candles, j)
                if cfg.break_even_after_r is not None:
                    trigger = entry + (1 if signal.side is Side.BUY else -1) * cfg.break_even_after_r * risk_distance
                    if (signal.side is Side.BUY and float(bar.high) >= trigger) or (signal.side is Side.SELL and float(bar.low) <= trigger):
                        stop = max(stop, entry) if signal.side is Side.BUY else min(stop, entry)
                if cfg.trailing_atr_multiple is not None and current_atr > 0:
                    candidate = float(bar.close) - current_atr * cfg.trailing_atr_multiple if signal.side is Side.BUY else float(bar.close) + current_atr * cfg.trailing_atr_multiple
                    stop = max(stop, candidate) if signal.side is Side.BUY else min(stop, candidate)

            hit_sl = float(bar.low) <= stop if signal.side is Side.BUY else float(bar.high) >= stop
            hit_target = next_target < len(targets) and (float(bar.high) >= targets[next_target] if signal.side is Side.BUY else float(bar.low) <= targets[next_target])
            if hit_sl and hit_target:
                # Conservative intrabar assumption: protective stop is reached first.
                exit_price, reason = stop, "stop_loss_first"
                realized += (exit_price - entry if signal.side is Side.BUY else entry - exit_price) * remaining
                weighted_exit += exit_price * remaining
                exited_units += remaining
                remaining = 0.0
                break
            if hit_sl:
                exit_price, reason = stop, "stop_loss"
                realized += (exit_price - entry if signal.side is Side.BUY else entry - exit_price) * remaining
                weighted_exit += exit_price * remaining
                exited_units += remaining
                remaining = 0.0
                break
            if hit_target:
                fraction = min(fractions[next_target], remaining / units) if fractions else 1.0
                qty = units * fraction
                qty = min(qty, remaining)
                exit_price = targets[next_target]
                realized += (exit_price - entry if signal.side is Side.BUY else entry - exit_price) * qty
                weighted_exit += exit_price * qty
                exited_units += qty
                remaining -= qty
                next_target += 1
                if remaining <= units * 1e-12:
                    reason = "take_profit_targets"
                    remaining = 0.0
                    break
            j += 1

        if remaining > 0:
            exit_price = float(candles.close.iloc[-1])
            realized += (exit_price - entry if signal.side is Side.BUY else entry - exit_price) * remaining
            weighted_exit += exit_price * remaining
            exited_units += remaining
        pnl_value = realized - model.round_trip_cost(units)
        average_exit = weighted_exit / exited_units if exited_units else exit_price
        if reason == "end_of_data" and next_target:
            reason = "partial_targets_end_of_data"
        trades.append(
            BacktestTrade(i, j, signal.side.value, entry, average_exit, initial_sl, initial_tp, units,
                          risk_amount, pnl_value, pnl_value / risk_amount, reason)
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
    return BacktestResult(count, wins, losses, sum(pnl_values), mdd,
                          wins / count if count else 0.0,
                          gross_wins / gross_losses if gross_losses else math.inf,
                          sum(pnl_values) / count if count else 0.0,
                          sum(r_values) / count if r_values else 0.0,
                          tuple(trades))
