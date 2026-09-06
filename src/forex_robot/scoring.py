from __future__ import annotations
from dataclasses import dataclass

DEFAULT_WEIGHTS={'trend':20,'momentum':15,'structure':20,'liquidity':15,'volatility':10,'session':10,'news':10}
@dataclass(frozen=True)
class ScoreResult:
    total:float
    verdict:str
    components:dict[str,float]

def score_signal(components:dict[str,float], weights:dict[str,float]|None=None)->ScoreResult:
    w=weights or DEFAULT_WEIGHTS
    if set(w)!=set(DEFAULT_WEIGHTS) or abs(sum(w.values())-100)>1e-9: raise ValueError('weights must contain all categories and sum to 100')
    total=sum(max(0,min(100,float(components.get(k,0))))*w[k]/100 for k in w)
    verdict='no_trade' if total<60 else 'watch' if total<70 else 'valid' if total<80 else 'strong' if total<90 else 'premium'
    return ScoreResult(round(total,2),verdict,{k:round(float(components.get(k,0)),2) for k in w})
