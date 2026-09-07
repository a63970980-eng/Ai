from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict

import pandas as pd

from forex_robot.backtest.engine import BacktestResult, run_backtest
from forex_robot.domain.models import Signal


class BacktestKwargs(TypedDict, total=False):
    spread: float
    slippage: float
    fee: float
    risk_per_trade: float
    execution_delay: int


@dataclass(frozen=True)
class Window:
    train_start: int
    train_end: int
    validation_end: int
    test_end: int


@dataclass(frozen=True)
class WalkForwardResult:
    window: Window
    validation: BacktestResult
    test: BacktestResult


def windows(n: int, train: int, validation: int, test: int, step: int | None = None) -> list[Window]:
    if min(train, validation, test) <= 0 or n < train + validation + test:
        return []
    step = step or test
    if step <= 0:
        raise ValueError("step must be positive")
    out: list[Window] = []
    start = 0
    while start + train + validation + test <= n:
        out.append(Window(start, start + train, start + train + validation, start + train + validation + test))
        start += step
    return out


def walk_forward(
    df: pd.DataFrame,
    train: int = 1000,
    validation: int = 250,
    test: int = 250,
    step: int | None = None,
) -> list[Window]:
    return windows(len(df), train, validation, test, step)


def evaluate_walk_forward(
    df: pd.DataFrame,
    signal_fn: Callable[[pd.DataFrame], Signal | None],
    train: int = 1000,
    validation: int = 250,
    test: int = 250,
    step: int | None = None,
    **backtest_kwargs: BacktestKwargs,
) -> list[WalkForwardResult]:
    results: list[WalkForwardResult] = []
    for window in windows(len(df), train, validation, test, step):
        validation_df = df.iloc[window.train_end:window.validation_end]
        test_df = df.iloc[window.validation_end:window.test_end]
        validation_result = run_backtest(validation_df, signal_fn, **backtest_kwargs)
        test_result = run_backtest(test_df, signal_fn, **backtest_kwargs)
        results.append(WalkForwardResult(window, validation_result, test_result))
    return results
