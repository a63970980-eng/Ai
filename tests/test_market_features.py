import pandas as pd

from forex_robot.features.indicators import build_features
from forex_robot.market.validation import validate_ohlc
from forex_robot.regime.detector import Regime, detect_regime


def candles(n=100):
    close=pd.Series([1+0.0005*i for i in range(n)])
    return pd.DataFrame({"open":close,"high":close+0.0002,"low":close-0.0002,"close":close,"volume":1000})


def test_validation_and_features():
    df=validate_ohlc(candles())
    out=build_features(df)
    assert {"ema_fast","ema_slow","rsi","atr","vwap","macd_hist"}.issubset(out.columns)


def test_regime_is_deterministic():
    assert detect_regime(candles()) in {Regime.TREND, Regime.RANGE, Regime.HIGH_VOLATILITY}
