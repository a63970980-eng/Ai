from __future__ import annotations

import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    previous = df.close.shift()
    tr = pd.concat(
        [(df.high - df.low), (df.high - previous).abs(), (df.low - previous).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    line = ema(close, 12) - ema(close, 26)
    signal = ema(line, 9)
    return line, signal, line - signal


def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    up = df.high.diff()
    down = -df.low.diff()
    plus = up.where((up > down) & (up > 0), 0.0)
    minus = down.where((down > up) & (down > 0), 0.0)
    average_true_range = atr(df, n).replace(0, np.nan)
    positive = 100 * plus.ewm(alpha=1 / n, adjust=False).mean() / average_true_range
    negative = 100 * minus.ewm(alpha=1 / n, adjust=False).mean() / average_true_range
    dx = 100 * (positive - negative).abs() / (positive + negative).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def bollinger(close: pd.Series, n: int = 20, k: float = 2) -> tuple[pd.Series, pd.Series, pd.Series]:
    mid = close.rolling(n).mean()
    std = close.rolling(n).std()
    return mid, mid + k * std, mid - k * std


def vwap(df: pd.DataFrame) -> pd.Series:
    volume = df.volume.replace(0, np.nan)
    return ((df.high + df.low + df.close) / 3 * volume).cumsum() / volume.cumsum()


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema20"] = ema(out.close, 20)
    out["ema50"] = ema(out.close, 50)
    out["ema200"] = ema(out.close, 200)
    out["rsi14"] = rsi(out.close)
    out["atr14"] = atr(out, 14)
    out["adx14"] = adx(out, 14)
    out["macd"], out["macd_signal"], out["macd_hist"] = macd(out.close)
    out["bb_mid"], out["bb_upper"], out["bb_lower"] = bollinger(out.close)
    out["vwap"] = vwap(out)
    out["volatility"] = out.close.pct_change().rolling(20).std()
    out["range"] = out.high - out.low

    # Stable semantic aliases retained for strategy and API consumers.
    out["ema_fast"] = out["ema20"]
    out["ema_slow"] = out["ema50"]
    out["rsi"] = out["rsi14"]
    out["atr"] = out["atr14"]
    return out
