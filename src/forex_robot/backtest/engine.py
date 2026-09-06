from __future__ import annotations
from dataclasses import dataclass
import math
import pandas as pd
from forex_robot.domain.models import Side
from forex_robot.backtest.execution_model import ExecutionModel

@dataclass(frozen=True)
class BacktestTrade:
    entry_index:int; exit_index:int; side:str; entry:float; exit:float; stop_loss:float; take_profit:float; pnl:float; r_multiple:float; exit_reason:str

@dataclass(frozen=True)
class BacktestResult:
    trades:int; wins:int; losses:int; net_pnl:float; max_drawdown:float; win_rate:float; profit_factor:float; expectancy:float=0.0; avg_r:float=0.0; trade_log:tuple[BacktestTrade,...]=()

def run_backtest(candles:pd.DataFrame, signal_fn, spread:float=0.0, slippage:float=0.0, fee:float=0.0, risk_per_trade:float=1.0, execution_delay:int=0)->BacktestResult:
    if candles.empty or len(candles)<2: return BacktestResult(0,0,0,0.0,0.0,0.0,math.inf)
    missing={"open","high","low","close"}-set(candles.columns)
    if missing: raise ValueError(f"missing OHLC columns: {sorted(missing)}")
    model=ExecutionModel(spread=spread,slippage=slippage,commission=fee); trades=[]; i=0
    while i<len(candles)-1:
        signal=signal_fn(candles.iloc[:i+1])
        if signal is None: i+=1; continue
        entry_i=min(i+max(0,execution_delay)+1,len(candles)-1); entry=model.entry_price(float(candles.close.iloc[entry_i]),signal.side.value)
        sl=float(signal.stop_loss); tp=float(signal.take_profit); risk_distance=max(abs(entry-sl),1e-12); j=entry_i; exit_price=float(candles.close.iloc[-1]); reason="end_of_data"
        while j<len(candles):
            bar=candles.iloc[j]
            if signal.side is Side.BUY:
                if float(bar.low)<=sl: exit_price,reason=sl,"stop_loss"; break
                if float(bar.high)>=tp: exit_price,reason=tp,"take_profit"; break
            else:
                if float(bar.high)>=sl: exit_price,reason=sl,"stop_loss"; break
                if float(bar.low)<=tp: exit_price,reason=tp,"take_profit"; break
            exit_price=float(bar.close); j+=1
        raw=exit_price-entry if signal.side is Side.BUY else entry-exit_price; pnl=raw-abs(fee); trades.append(BacktestTrade(i,j,signal.side.value,entry,exit_price,sl,tp,pnl,pnl/risk_distance,reason)); i=max(j+1,i+1)
    pnl=[t.pnl for t in trades]; rvals=[t.r_multiple for t in trades]; equity=peak=mdd=0.0
    for value in pnl: equity+=value; peak=max(peak,equity); mdd=max(mdd,peak-equity)
    wins=sum(x>0 for x in pnl); losses=sum(x<0 for x in pnl); gw=sum(x for x in pnl if x>0); gl=-sum(x for x in pnl if x<0)
    return BacktestResult(len(pnl),wins,losses,sum(pnl),mdd,wins/len(pnl) if pnl else 0.0,gw/gl if gl else math.inf,sum(pnl)/len(pnl) if pnl else 0.0,sum(rvals)/len(rvals) if rvals else 0.0,tuple(trades))
