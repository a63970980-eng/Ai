from __future__ import annotations

import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series: return s.ewm(span=n, adjust=False).mean()
def sma(s: pd.Series, n: int) -> pd.Series: return s.rolling(n).mean()

def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df.close.shift()
    tr = pd.concat([(df.high-df.low), (df.high-prev).abs(), (df.low-prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    line = ema(close, 12) - ema(close, 26)
    signal = ema(line, 9)
    return line, signal, line-signal

def vwap(df: pd.DataFrame) -> pd.Series:
    vol = df.volume.replace(0, np.nan)
    return ((df.high + df.low + df.close) / 3 * vol).cumsum() / vol.cumsum()

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema_fast"] = ema(out.close, 9)
    out["ema_slow"] = ema(out.close, 21)
    out["rsi"] = rsi(out.close)
    out["atr"] = atr(out)
    out["vwap"] = vwap(out)
    out["macd"], out["macd_signal"], out["macd_hist"] = macd(out.close)
    out["volatility"] = out.close.pct_change().rolling(20).std()
    return out
