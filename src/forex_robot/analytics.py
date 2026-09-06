from __future__ import annotations
import math
import numpy as np

def analytics(returns:list[float], periods_per_year:int=252)->dict[str,float]:
    if not returns: return {'trades':0,'win_rate':0.,'profit_factor':0.,'expectancy':0.,'sharpe':0.,'sortino':0.,'max_drawdown':0.,'recovery_factor':0.,'avg_r':0.}
    x=np.asarray(returns,float); wins=x[x>0]; losses=x[x<0]; equity=np.cumsum(x); peak=np.maximum.accumulate(equity); dd=peak-equity; mdd=float(dd.max(initial=0)); mean=float(x.mean()); sd=float(x.std(ddof=1)) if len(x)>1 else 0.; downside=float(np.sqrt(np.mean(np.minimum(x,0)**2)))
    pf=float(wins.sum()/-losses.sum()) if losses.size else math.inf
    return {'trades':int(len(x)),'win_rate':float(np.mean(x>0)),'profit_factor':pf,'expectancy':mean,'sharpe':mean/sd*math.sqrt(periods_per_year) if sd else 0.,'sortino':mean/downside*math.sqrt(periods_per_year) if downside else 0.,'max_drawdown':mdd,'recovery_factor':float(x.sum()/mdd) if mdd else math.inf,'avg_r':mean}
