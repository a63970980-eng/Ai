from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Exposure:
    base: dict[str,float]
    quote: dict[str,float]
    gross: float
    net: float

def currency_exposure(positions:list[dict]) -> Exposure:
    base:dict[str,float]={}; quote:dict[str,float]={}
    for p in positions:
        pair=str(p.get('symbol','')).upper().replace('/','')
        if len(pair)!=6: continue
        units=abs(float(p.get('units',0))); sign=1.0 if str(p.get('side','buy')).lower()=='buy' else -1.0
        b,q=pair[:3],pair[3:]
        base[b]=base.get(b,0)+sign*units; quote[q]=quote.get(q,0)-sign*units
    gross=sum(abs(v) for v in base.values())+sum(abs(v) for v in quote.values())
    net=sum(base.values())+sum(quote.values())
    return Exposure(base,quote,gross,net)

def correlation_breach(correlation:float, threshold:float=.85)->bool:
    return abs(correlation)>=threshold
