from enum import StrEnum

import pandas as pd

from forex_robot.features.indicators import atr, ema


class Regime(StrEnum):
    TREND = "trend"
    RANGE = "range"
    HIGH_VOLATILITY = "high_volatility"
    UNKNOWN = "unknown"


def detect_regime(df: pd.DataFrame) -> Regime:
    if len(df) < 60:
        return Regime.UNKNOWN
    e9, e21 = ema(df.close, 9), ema(df.close, 21)
    a = atr(df, 14)
    if a.iloc[-1] > a.rolling(50).mean().iloc[-1] * 1.8:
        return Regime.HIGH_VOLATILITY
    separation = abs(e9.iloc[-1] - e21.iloc[-1]) / max(df.close.iloc[-1], 1e-12)
    slope = abs(e21.iloc[-1] - e21.iloc[-10]) / max(df.close.iloc[-1], 1e-12)
    if separation > 0.0005 and slope > 0.0003:
        return Regime.TREND
    return Regime.RANGE
