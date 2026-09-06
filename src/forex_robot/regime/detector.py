from enum import StrEnum
import pandas as pd
from forex_robot.features.indicators import adx, atr, ema

class Regime(StrEnum):
    TREND='trend'; RANGE='range'; HIGH_VOLATILITY='high_volatility'; LOW_VOLATILITY='low_volatility'; UNKNOWN='unknown'

def detect_regime(df:pd.DataFrame)->Regime:
    if len(df)<200:return Regime.UNKNOWN
    e20,e50,e200=ema(df.close,20),ema(df.close,50),ema(df.close,200)
    a=atr(df,14); ad=adx(df,14)
    atr_now=float(a.iloc[-1]); atr_base=float(a.rolling(50).median().iloc[-1])
    if not pd.notna(atr_now) or not pd.notna(atr_base) or atr_base<=0:return Regime.UNKNOWN
    if atr_now>atr_base*1.8:return Regime.HIGH_VOLATILITY
    if atr_now<atr_base*.55:return Regime.LOW_VOLATILITY
    if float(ad.iloc[-1])>=22 and (float(e20.iloc[-1])>float(e50.iloc[-1])>float(e200.iloc[-1]) or float(e20.iloc[-1])<float(e50.iloc[-1])<float(e200.iloc[-1])):return Regime.TREND
    return Regime.RANGE
