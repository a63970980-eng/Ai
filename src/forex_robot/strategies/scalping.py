from __future__ import annotations

import pandas as pd
from forex_robot.domain.models import Side, Signal
from forex_robot.features.indicators import atr, ema, rsi


def _signal(symbol: str, side: Side, price: float, a: float, reason: str, confidence: float) -> Signal | None:
    if not pd.notna(a) or a <= 0:
        return None
    risk = max(a * 1.2, price * 0.0005)
    if side is Side.BUY:
        stop, target = price - risk, price + risk * 1.6
    else:
        stop, target = price + risk, price - risk * 1.6
    return Signal(symbol=symbol, side=side, confidence=min(confidence, .99), entry=price,
                  stop_loss=stop, take_profit=target, reason=reason,
                  timestamp=pd.Timestamp.now(tz="UTC").to_pydatetime())


def momentum(symbol: str, df: pd.DataFrame) -> Signal | None:
    if len(df) < 30: return None
    f, s = ema(df.close, 9).iloc[-1], ema(df.close, 21).iloc[-1]
    rr = rsi(df.close).iloc[-1]
    if f > s and 52 < rr < 72: return _signal(symbol, Side.BUY, float(df.close.iloc[-1]), float(atr(df).iloc[-1]), "EMA momentum confirmation", .70)
    if f < s and 28 < rr < 48: return _signal(symbol, Side.SELL, float(df.close.iloc[-1]), float(atr(df).iloc[-1]), "EMA momentum confirmation", .70)
    return None


def mean_reversion(symbol: str, df: pd.DataFrame) -> Signal | None:
    if len(df) < 30: return None
    rr = rsi(df.close).iloc[-1]; price = float(df.close.iloc[-1]); a = float(atr(df).iloc[-1])
    if rr < 25: return _signal(symbol, Side.BUY, price, a, "oversold mean reversion", .68)
    if rr > 75: return _signal(symbol, Side.SELL, price, a, "overbought mean reversion", .68)
    return None


def breakout(symbol: str, df: pd.DataFrame) -> Signal | None:
    if len(df) < 25: return None
    hi, lo = df.high.iloc[-21:-1].max(), df.low.iloc[-21:-1].min(); price=float(df.close.iloc[-1]); a=float(atr(df).iloc[-1])
    if price > hi: return _signal(symbol, Side.BUY, price, a, "20-bar upside breakout", .72)
    if price < lo: return _signal(symbol, Side.SELL, price, a, "20-bar downside breakout", .72)
    return None


def trend(symbol: str, df: pd.DataFrame) -> Signal | None:
    if len(df) < 210: return None
    e50, e200 = ema(df.close, 50).iloc[-1], ema(df.close, 200).iloc[-1]
    price, a = float(df.close.iloc[-1]), float(atr(df).iloc[-1])
    if e50 > e200 and price > e50:
        return _signal(symbol, Side.BUY, price, a, "EMA50/200 trend alignment", .74)
    if e50 < e200 and price < e50:
        return _signal(symbol, Side.SELL, price, a, "EMA50/200 trend alignment", .74)
    return None


def liquidity(symbol: str, df: pd.DataFrame) -> Signal | None:
    if len(df) < 25: return None
    price, a = float(df.close.iloc[-1]), float(atr(df).iloc[-1])
    prior_high = float(df.high.iloc[-21:-1].max())
    prior_low = float(df.low.iloc[-21:-1].min())
    bar_high, bar_low = float(df.high.iloc[-1]), float(df.low.iloc[-1])
    if bar_high > prior_high and price < prior_high:
        return _signal(symbol, Side.SELL, price, a, "buy-side liquidity sweep and rejection", .73)
    if bar_low < prior_low and price > prior_low:
        return _signal(symbol, Side.BUY, price, a, "sell-side liquidity sweep and rejection", .73)
    return None


def scalping(symbol: str, df: pd.DataFrame) -> Signal | None:
    return momentum(symbol, df)
