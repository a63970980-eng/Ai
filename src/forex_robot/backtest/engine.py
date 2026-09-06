from __future__ import annotations
from dataclasses import dataclass
import math
import pandas as pd
from forex_robot.domain.models import Side

@dataclass(frozen=True)
class BacktestResult:
    trades:int; wins:int; losses:int; net_pnl:float; max_drawdown:float; win_rate:float; profit_factor:float
    expectancy:float=0.0; avg_r:float=0.0

def run_backtest(candles:pd.DataFrame, signal_fn, spread:float=0.0, slippage:float=0.0, fee:float=0.0, risk_per_trade:float=1.0)->BacktestResult:
    pnl=[]; rvals=[]; equity=0.; peak=0.; mdd=0.
    for i in range(len(candles)-1):
        signal=signal_fn(candles.iloc[:i+1])
        if signal is None: continue
        entry=float(signal.entry); sl=float(signal.stop_loss); tp=float(signal.take_profit); side=signal.side
        if side is Side.BUY: entry+=spread/2+slippage; hit_sl=candles.low.iloc[i+1]<=sl; hit_tp=candles.high.iloc[i+1]>=tp; exitp=sl if hit_sl else tp if hit_tp else float(candles.close.iloc[i+1]); raw=exitp-entry
        else: entry-=spread/2+slippage; hit_sl=candles.high.iloc[i+1]>=sl; hit_tp=candles.low.iloc[i+1]<=tp; exitp=sl if hit_sl else tp if hit_tp else float(candles.close.iloc[i+1]); raw=entry-exitp
        cost=fee; result=raw-cost; pnl.append(result); risk=max(abs(entry-sl),1e-12); r=result/risk; rvals.append(r); equity+=result; peak=max(peak,equity); mdd=max(mdd,peak-equity)
    wins=sum(x>0 for x in pnl); losses=len(pnl)-wins; gw=sum(x for x in pnl if x>0); gl=-sum(x for x in pnl if x<0)
    return BacktestResult(len(pnl),wins,losses,sum(pnl),mdd,wins/len(pnl) if pnl else 0.,gw/gl if gl else math.inf,sum(pnl)/len(pnl) if pnl else 0.,sum(rvals)/len(rvals) if rvals else 0.)
