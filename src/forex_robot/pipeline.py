from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from forex_robot.features.indicators import adx, ema, rsi
from forex_robot.market.liquidity import analyze_liquidity
from forex_robot.market.structure import detect_structure
from forex_robot.market.multitimeframe import build_mtf
from forex_robot.scoring import score_signal

@dataclass(frozen=True)
class PipelineDecision:
    allowed:bool; stage:str; score:float; verdict:str; reason:str

def evaluate_pipeline(df_1m:pd.DataFrame, weights=None)->PipelineDecision:
    mtf=build_mtf(df_1m)
    if min(len(mtf['15m']),len(mtf['5m']),len(mtf['1m']))<30:return PipelineDecision(False,'data',0,'no_trade','insufficient multi-timeframe history')
    f15=mtf['15m']; f5=mtf['5m']; f1=mtf['1m']; e20,e50=ema(f15.close,20).iloc[-1],ema(f15.close,50).iloc[-1]; direction='buy' if e20>e50 else 'sell'
    c5=float(f5.close.iloc[-1]); m5='buy' if ema(f5.close,20).iloc[-1]>ema(f5.close,50).iloc[-1] else 'sell'
    if m5!=direction:return PipelineDecision(False,'5m_confirmation',0,'no_trade','5M disagrees with 15M direction')
    s=detect_structure(f5); l=analyze_liquidity(f5); rr=float(rsi(f1.close).iloc[-1]); ad=float(adx(f5).iloc[-1])
    comps={'trend':85 if direction==m5 else 30,'momentum':85 if ((direction=='buy' and rr>50) or (direction=='sell' and rr<50)) else 35,'structure':85 if s.trend==('bullish' if direction=='buy' else 'bearish') else 55,'liquidity':90 if l.sweep else 60,'volatility':70 if ad>=15 else 50,'session':70,'news':100}
    score=score_signal(comps,weights)
    return PipelineDecision(score.total>=70,'ai_score',score.total,score.verdict,'pipeline approved' if score.total>=70 else 'score below execution threshold')
