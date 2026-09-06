from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from forex_robot.domain.models import Signal, Side
from forex_robot.features.indicators import adx, atr, ema, rsi
from forex_robot.market.liquidity import analyze_liquidity
from forex_robot.market.structure import detect_structure

@dataclass(frozen=True)
class StrategySignal:
    name: str
    signal: Signal
    score: float

def _signal(symbol:str, side:Side, price:float, atr_value:float, name:str, confidence:float)->Signal:
    d=max(atr_value*1.25, price*0.0004)
    sl=price-d if side is Side.BUY else price+d
    tp=price+2*d if side is Side.BUY else price-2*d
    return Signal(symbol=symbol,side=side,confidence=confidence,entry=price,stop_loss=sl,take_profit=tp,reason=name,timestamp=pd.Timestamp.utcnow().to_pydatetime())

def generate(symbol:str, df:pd.DataFrame)->list[StrategySignal]:
    if len(df)<200: return []
    price=float(df.close.iloc[-1]); a=float(atr(df,14).iloc[-1]); e20=float(ema(df.close,20).iloc[-1]); e50=float(ema(df.close,50).iloc[-1]); e200=float(ema(df.close,200).iloc[-1]); r=float(rsi(df.close,14).iloc[-1]); ad=float(adx(df,14).iloc[-1])
    st=detect_structure(df); li=analyze_liquidity(df)
    out=[]
    if e20>e50>e200 and ad>=20 and r>=50:
        out.append(StrategySignal('trend',_signal(symbol,Side.BUY,price,a,'trend_alignment',.74),.74))
    if e20<e50<e200 and ad>=20 and r<=50:
        out.append(StrategySignal('trend',_signal(symbol,Side.SELL,price,a,'trend_alignment',.74),.74))
    if r<30 and price<=float(df.close.rolling(20).min().iloc[-1]):
        out.append(StrategySignal('mean_reversion',_signal(symbol,Side.BUY,price,a,'oversold_reversion',.68),.68))
    if r>70 and price>=float(df.close.rolling(20).max().iloc[-1]):
        out.append(StrategySignal('mean_reversion',_signal(symbol,Side.SELL,price,a,'overbought_reversion',.68),.68))
    if li.sweep=='sell_side_sweep' and st.trend in {'bullish','range'}:
        out.append(StrategySignal('liquidity',_signal(symbol,Side.BUY,price,a,'sell_side_sweep',.78),.78))
    if li.sweep=='buy_side_sweep' and st.trend in {'bearish','range'}:
        out.append(StrategySignal('liquidity',_signal(symbol,Side.SELL,price,a,'buy_side_sweep',.78),.78))
    return out

def ensemble(symbol:str, df:pd.DataFrame)->StrategySignal|None:
    signals=generate(symbol,df)
    if not signals: return None
    signals.sort(key=lambda x:x.score,reverse=True)
    best=signals[0]
    return best
