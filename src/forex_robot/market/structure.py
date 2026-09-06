from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class Swing:
    index: int
    price: float
    kind: str

@dataclass(frozen=True)
class StructureState:
    trend: str
    last_swing_high: float | None
    last_swing_low: float | None
    event: str

def detect_structure(df: pd.DataFrame, window: int = 2) -> StructureState:
    if len(df) < window * 2 + 3:
        return StructureState('unknown', None, None, 'insufficient_data')
    highs: list[float] = []; lows: list[float] = []
    for i in range(window, len(df)-window):
        h=float(df.high.iloc[i]); l=float(df.low.iloc[i])
        if h >= float(df.high.iloc[i-window:i+window+1].max()): highs.append(h)
        if l <= float(df.low.iloc[i-window:i+window+1].min()): lows.append(l)
    sh, sl = (highs[-1] if highs else None), (lows[-1] if lows else None)
    prev_h = highs[-2] if len(highs)>1 else None; prev_l = lows[-2] if len(lows)>1 else None
    close=float(df.close.iloc[-1]); trend='range'
    if sh is not None and sl is not None:
        if close > sh: trend='bullish'; event='BOS_UP'
        elif close < sl: trend='bearish'; event='BOS_DOWN'
        elif prev_h is not None and prev_l is not None and sh>prev_h and sl>prev_l: trend='bullish'; event='HH_HL'
        elif prev_h is not None and prev_l is not None and sh<prev_h and sl<prev_l: trend='bearish'; event='LH_LL'
        else: event='range'
    else: event='range'
    return StructureState(trend, sh, sl, event)
