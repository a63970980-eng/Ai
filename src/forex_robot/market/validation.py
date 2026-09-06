from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ValidationReport:
    rows: int
    duplicates: int
    gaps: int
    anomalies: int


def validate_ohlc(df: pd.DataFrame, timeframe: str | None = None) -> pd.DataFrame:
    required = {"open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    out = df.copy()
    if out.empty:
        out.attrs["validation"] = ValidationReport(0, 0, 0, 0)
        return out
    if not isinstance(out.index, pd.DatetimeIndex):
        out.index = pd.to_datetime(out.index, utc=True)
    elif out.index.tz is None:
        out.index = out.index.tz_localize("UTC")
    else:
        out.index = out.index.tz_convert("UTC")
    out = out.sort_index()
    duplicates = int(out.index.duplicated(keep="last").sum())
    if duplicates:
        out = out[~out.index.duplicated(keep="last")]
    prices = ["open", "high", "low", "close"]
    if out[prices].isna().any().any():
        raise ValueError("OHLC contains nulls")
    if (out[prices] <= 0).any().any():
        raise ValueError("prices must be positive")
    anomalies = int((out.high < out.low).sum())
    anomalies += int((out.high < out[["open", "close"]].max(axis=1)).sum())
    anomalies += int((out.low > out[["open", "close"]].min(axis=1)).sum())
    if anomalies:
        raise ValueError("invalid OHLC range")
    gaps = 0
    if timeframe:
        expected = pd.Timedelta(timeframe)
        gaps = int((out.index.to_series().diff() > expected * 1.5).sum())
    out.attrs["validation"] = ValidationReport(len(out), duplicates, gaps, anomalies)
    return out


def validate_tick(symbol: str, bid: float, ask: float) -> None:
    if not symbol or bid <= 0 or ask <= 0 or ask < bid:
        raise ValueError("invalid tick")
