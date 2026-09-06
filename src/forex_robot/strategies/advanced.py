from __future__ import annotations
import pandas as pd
from forex_robot.domain.models import Side, Signal
from forex_robot.features.indicators import atr, ema, rsi
from forex_robot.market.structure import detect_structure
from forex_robot.market.liquidity import analyze_liquidity

def make_signal(symbol,side,price,a,reason,confidence):
    d=max(a*1.2,price*0.0005); sl=price-d if side is Side.BUY else price+d; tp=price+d*2 if side is Side.BUY else price-d*2
    return Signal(symbol=symbol,side=side,confidence=min(.99,confidence),entry=price,stop_loss=sl,take_profit=tp,reason=reason,timestamp=pd.Timestamp.now(tz='UTC').to_pydatetime())

def trend(symbol,df):
    if len(df)<200:return None
    e20,e50,e200=ema(df.close,20).iloc[-1],ema(df.close,50).iloc[-1],ema(df.close,200).iloc[-1]; p=float(df.close.iloc[-1]); a=float(atr(df).iloc[-1])
    if e20>e50>e200:return make_signal(symbol,Side.BUY,p,a,'EMA20/50/200 trend alignment',.74)
    if e20<e50<e200:return make_signal(symbol,Side.SELL,p,a,'EMA20/50/200 trend alignment',.74)
    return None

def momentum(symbol,df):
    if len(df)<30:return None
    rr=float(rsi(df.close).iloc[-1]); p=float(df.close.iloc[-1]); a=float(atr(df).iloc[-1])
    if rr>55 and rr<75:return make_signal(symbol,Side.BUY,p,a,'RSI momentum',.70)
    if rr<45 and rr>25:return make_signal(symbol,Side.SELL,p,a,'RSI momentum',.70)
    return None

def liquidity(symbol,df):
    if len(df)<30:return None
    l=analyze_liquidity(df); s=detect_structure(df); p=float(df.close.iloc[-1]); a=float(atr(df).iloc[-1])
    if l.sweep=='sell_side_sweep' and s.trend!='bearish': return make_signal(symbol,Side.BUY,p,a,'sell-side liquidity sweep with structure confirmation',.78)
    if l.sweep=='buy_side_sweep' and s.trend!='bullish': return make_signal(symbol,Side.SELL,p,a,'buy-side liquidity sweep with structure confirmation',.78)
    return None
