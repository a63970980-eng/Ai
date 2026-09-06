from __future__ import annotations
import numpy as np

def monte_carlo(trade_returns:list[float], simulations:int=5000, seed:int=42, ruin_fraction:float=0.5)->dict[str,float]:
    if not trade_returns or simulations<=0: return {'median_final':0.0,'p05_final':0.0,'p95_final':0.0,'prob_loss':0.0,'p95_drawdown':0.0,'p95_losing_streak':0.0,'risk_of_ruin':0.0}
    if not 0<ruin_fraction<=1: raise ValueError('ruin_fraction must be in (0, 1]')
    rng=np.random.default_rng(seed); arr=np.asarray(trade_returns,dtype=float); paths=rng.choice(arr,(simulations,len(arr)),replace=True); finals=paths.sum(axis=1); dds=[]; streaks=[]; ruined=0
    starting=float(np.sum(np.maximum(-arr,0))*max(len(arr),1)+1.0); ruin_level=-starting*ruin_fraction
    for p in paths:
        eq=np.cumsum(p); peak=np.maximum.accumulate(eq); dds.append(float((peak-eq).max(initial=0.0))); cur=best=0
        for v in p: cur=cur+1 if v<0 else 0; best=max(best,cur)
        streaks.append(best); ruined += int(float(np.min(eq,initial=0.0))<=ruin_level)
    return {'median_final':float(np.median(finals)),'p05_final':float(np.quantile(finals,.05)),'p95_final':float(np.quantile(finals,.95)),'prob_loss':float(np.mean(finals<0)),'p95_drawdown':float(np.quantile(dds,.95)),'p95_losing_streak':float(np.quantile(streaks,.95)),'risk_of_ruin':float(ruined/simulations)}
