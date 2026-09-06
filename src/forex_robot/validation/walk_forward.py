from __future__ import annotations

import pandas as pd


def walk_forward(df: pd.DataFrame, backtest_fn, train_size: int, test_size: int, step: int | None = None):
    """Run sequential out-of-sample windows; each test slice occurs strictly after its train slice."""
    if train_size <= 0 or test_size <= 0: raise ValueError("window sizes must be positive")
    step = step or test_size
    results=[]; start=0
    while start + train_size + test_size <= len(df):
        train=df.iloc[start:start+train_size]
        test=df.iloc[start+train_size:start+train_size+test_size]
        results.append({"train_start":start,"train_end":start+train_size,"test_start":start+train_size,"test_end":start+train_size+test_size,"result":backtest_fn(test)})
        start += step
    return results
