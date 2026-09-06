from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class StressResult:
    scenario:str; net_pnl:float; max_drawdown:float

def stress_returns(returns:list[float], spread_factor:float=1.5, slippage_factor:float=1.5, volatility_factor:float=1.0, seed:int=42)->StressResult:
    if not returns: return StressResult('empty',0.,0.)
    rng=np.random.default_rng(seed); x=np.asarray(returns,float)*volatility_factor
    costs=(abs(x).mean()*0.01)*(spread_factor+slippage_factor-2); x=x-costs; eq=np.cumsum(x); peak=np.maximum.accumulate(eq); return StressResult('spread_slippage_volatility',float(eq[-1]),float((peak-eq).max(initial=0)))

def connection_failure()->dict[str,str]: return {'action':'halt_new_orders','preserve':'open_position_state','recovery':'reconcile broker before resume'}
