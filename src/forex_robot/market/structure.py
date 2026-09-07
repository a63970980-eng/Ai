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
    choch: str | None = None
    retest: bool = False
    swing_highs: tuple[float, ...] = ()
    swing_lows: tuple[float, ...] = ()


def detect_structure(df: pd.DataFrame, window: int = 2) -> StructureState:
    if len(df) < window * 2 + 3 or window < 1:
        return StructureState("unknown", None, None, "insufficient_data")

    highs: list[float] = []
    lows: list[float] = []
    for i in range(window, len(df) - window):
        h = float(df.high.iloc[i])
        l = float(df.low.iloc[i])
        local_high = float(df.high.iloc[i - window : i + window + 1].max())
        local_low = float(df.low.iloc[i - window : i + window + 1].min())
        if h >= local_high:
            highs.append(h)
        if l <= local_low:
            lows.append(l)

    sh = highs[-1] if highs else None
    sl = lows[-1] if lows else None
    prev_h = highs[-2] if len(highs) > 1 else None
    prev_l = lows[-2] if len(lows) > 1 else None
    close = float(df.close.iloc[-1])
    trend = "range"
    event = "range"
    choch: str | None = None
    retest = False

    if sh is not None and sl is not None:
        bullish_structure = prev_h is not None and prev_l is not None and sh > prev_h and sl > prev_l
        bearish_structure = prev_h is not None and prev_l is not None and sh < prev_h and sl < prev_l
        if close > sh:
            trend, event = "bullish", "BOS_UP"
            if bearish_structure:
                choch = "bullish"
        elif close < sl:
            trend, event = "bearish", "BOS_DOWN"
            if bullish_structure:
                choch = "bearish"
        elif bullish_structure:
            trend, event = "bullish", "HH_HL"
        elif bearish_structure:
            trend, event = "bearish", "LH_LL"

        # A retest is a current-bar interaction with the most recently broken level.
        recent_high = prev_h if event == "BOS_UP" else sh
        recent_low = prev_l if event == "BOS_DOWN" else sl
        current_high = float(df.high.iloc[-1])
        current_low = float(df.low.iloc[-1])
        if event == "BOS_UP" and recent_high is not None:
            retest = current_low <= recent_high <= current_high and close >= recent_high
        elif event == "BOS_DOWN" and recent_low is not None:
            retest = current_low <= recent_low <= current_high and close <= recent_low

    return StructureState(
        trend,
        sh,
        sl,
        event,
        choch,
        retest,
        tuple(highs[-5:]),
        tuple(lows[-5:]),
    )
