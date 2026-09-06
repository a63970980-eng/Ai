from __future__ import annotations
from dataclasses import dataclass
from forex_robot.domain.models import Side

@dataclass(frozen=True)
class ExitPlan:
    stop_loss:float; take_profits:list[float]; break_even_trigger_r:float=1.0; trail_atr:float=1.5

def build_exit_plan(side:Side, entry:float, atr_value:float, risk_distance:float|None=None)->ExitPlan:
    d=max(float(risk_distance or 0),float(atr_value)*1.25)
    if side is Side.BUY:
        sl=entry-d; tps=[entry+d,entry+1.5*d,entry+2*d,entry+3*d]
    else:
        sl=entry+d; tps=[entry-d,entry-1.5*d,entry-2*d,entry-3*d]
    return ExitPlan(sl,tps)

def trailing_stop(side:Side, current:float, atr_value:float, multiplier:float=1.5, existing:float|None=None)->float:
    candidate=current-float(atr_value)*multiplier if side is Side.BUY else current+float(atr_value)*multiplier
    if existing is None: return candidate
    return max(existing,candidate) if side is Side.BUY else min(existing,candidate)
