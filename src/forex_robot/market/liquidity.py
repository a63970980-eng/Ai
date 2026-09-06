from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class LiquidityState:
    buy_side: float | None
    sell_side: float | None
    equal_highs: bool
    equal_lows: bool
    sweep: str | None
    fvg: str | None

def analyze_liquidity(df: pd.DataFrame, lookback: int = 20, tolerance: float = 0.00015) -> LiquidityState:
    if len(df) < 5: return LiquidityState(None,None,False,False,None,None)
    x=df.tail(lookback); bh=float(x.high.max()); bl=float(x.low.min());
    highs=x.high.to_numpy(); lows=x.low.to_numpy()
    eqh=abs(highs[-1]-highs[-2]) <= tolerance*max(highs[-1],1) if len(highs)>1 else False
    eql=abs(lows[-1]-lows[-2]) <= tolerance*max(lows[-1],1) if len(lows)>1 else False
    last=df.iloc[-1]; prev=df.iloc[-2]
    sweep=None
    if float(last.high)>float(x.high.iloc[:-1].max()) and float(last.close)<float(prev.close): sweep='buy_side_sweep'
    elif float(last.low)<float(x.low.iloc[:-1].min()) and float(last.close)>float(prev.close): sweep='sell_side_sweep'
    fvg=None
    if len(df)>=3:
        a,b,c=df.iloc[-3],df.iloc[-2],df.iloc[-1]
        if float(a.high)<float(c.low): fvg='bullish'
        elif float(a.low)>float(c.high): fvg='bearish'
    return LiquidityState(bh,bl,eqh,eql,sweep,fvg)
