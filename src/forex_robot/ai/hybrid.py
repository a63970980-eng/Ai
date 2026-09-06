from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class ModelPrediction:
    model:str; score:float; rationale:str

def statistical_score(features:dict[str,float])->ModelPrediction:
    trend=float(features.get('trend',0)); momentum=float(features.get('momentum',0)); structure=float(features.get('structure',0)); volatility=float(features.get('volatility',50))
    score=max(0,min(100,50+0.30*trend+0.25*momentum+0.25*structure-0.20*abs(volatility-50)))
    return ModelPrediction('deterministic_statistical_baseline',round(score,2),'bounded feature ensemble; never overrides risk controls')

def anomaly_score(features:dict[str,float])->float:
    vals=[float(v) for v in features.values() if math.isfinite(float(v))]
    if not vals: return 0.0
    return min(100.0,abs(sum(vals)/len(vals)))

class AIReasoningBoundary:
    def select(self, predictions:list[ModelPrediction])->ModelPrediction|None:
        if not predictions:return None
        return max(predictions,key=lambda p:p.score)
