from dataclasses import dataclass
from .config import settings
from .models import Decision,Side
@dataclass
class RiskState:
    equity:float=100000.;day_start:float=100000.;peak:float=100000.;open_positions:int=0;kill_switch:bool=False
def decide(symbol,price,opinions,state):
    v=[o for o in opinions if not o.error and o.confidence>=settings.ai_min_confidence]
    if not v:return Decision(symbol,Side.WAIT,0,0,price,price,price,0,["no_ai_consensus"],opinions)
    votes={Side.BUY:0.,Side.SELL:0.,Side.WAIT:0.}
    for o in v:votes[o.side]+=o.confidence*o.score
    side=max(votes,key=votes.get);total=sum(votes.values());conf=votes[side]/total if total else 0
    if side==Side.WAIT or conf<.60:return Decision(symbol,Side.WAIT,conf,conf*100,price,price,price,0,["weak_consensus"],opinions)
    sl=price*.992 if side==Side.BUY else price*1.008;tp=price*1.016 if side==Side.BUY else price*.984
    daily=max(0,(state.day_start-state.equity)/state.day_start);dd=max(0,(state.peak-state.equity)/state.peak)
    ok=not state.kill_switch and daily<settings.max_daily_loss and dd<settings.max_drawdown and state.open_positions<settings.max_open_positions
    return Decision(symbol,side,conf,conf*100,price,sl,tp,min(settings.max_risk_per_trade,.005),[] if ok else ["risk_gate"],opinions,ok)
