from __future__ import annotations

import pandas as pd


def validate_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    required={"open","high","low","close"}
    missing=required-set(df.columns)
    if missing: raise ValueError(f"missing columns: {sorted(missing)}")
    out=df.copy()
    if out.empty: return out
    if (out[["open","high","low","close"]] <= 0).any().any(): raise ValueError("prices must be positive")
    if (out.high < out.low).any(): raise ValueError("high cannot be below low")
    if (out.high < out[["open","close"]].max(axis=1)).any(): raise ValueError("high must cover open/close")
    if (out.low > out[["open","close"]].min(axis=1)).any(): raise ValueError("low must cover open/close")
    if not out.index.is_monotonic_increasing: out=out.sort_index()
    return out.drop_duplicates()
