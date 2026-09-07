from __future__ import annotations

from enum import StrEnum

import pandas as pd

from forex_robot.features.indicators import adx, atr, ema


class Regime(StrEnum):
    TREND = "trend"
    RANGE = "range"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNKNOWN = "unknown"


def detect_regime(df: pd.DataFrame) -> Regime:
    """Classify the current market regime without requiring future observations."""
    if len(df) < 60:
        return Regime.UNKNOWN

    e20 = ema(df.close, 20)
    e50 = ema(df.close, 50)
    e200 = ema(df.close, 200)
    average_true_range = atr(df, 14)
    adx_values = adx(df, 14)

    atr_now = float(average_true_range.iloc[-1])
    baseline_window = average_true_range.iloc[-50:]
    atr_base = float(baseline_window.median())
    if not pd.notna(atr_now) or not pd.notna(atr_base) or atr_base <= 0:
        return Regime.UNKNOWN

    if atr_now > atr_base * 1.8:
        return Regime.HIGH_VOLATILITY
    if atr_now < atr_base * 0.55:
        return Regime.LOW_VOLATILITY

    adx_now = float(adx_values.iloc[-1])
    fast = float(e20.iloc[-1])
    slow = float(e50.iloc[-1])
    long_term = float(e200.iloc[-1])
    aligned_trend = (fast > slow > long_term) or (fast < slow < long_term)

    # With short histories EMA200 is still well-defined via its recursive form.
    # Use directional alignment plus ADX; a fallback slope keeps deterministic
    # synthetic/early datasets from being mislabeled UNKNOWN.
    if pd.notna(adx_now) and adx_now >= 22 and aligned_trend:
        return Regime.TREND

    slope = float(e20.iloc[-1] - e20.iloc[-20])
    if abs(slope) > atr_now * 0.5 and aligned_trend:
        return Regime.TREND

    return Regime.RANGE
