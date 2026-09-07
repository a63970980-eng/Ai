from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone

import pandas as pd

from forex_robot.features.indicators import adx, atr, ema, rsi
from forex_robot.market.liquidity import analyze_liquidity
from forex_robot.market.multitimeframe import Session, build_mtf, classify_session
from forex_robot.market.structure import detect_structure
from forex_robot.scoring import score_signal


@dataclass(frozen=True)
class PipelineDecision:
    allowed: bool
    stage: str
    score: float
    verdict: str
    reason: str


def _session_score(df: pd.DataFrame) -> float:
    ts = pd.Timestamp(df.index[-1]).to_pydatetime()
    session = classify_session(ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc))
    return 100.0 if session in {Session.LONDON_NY_OVERLAP, Session.LONDON, Session.NEW_YORK} else 60.0 if session is Session.ASIA else 30.0


def evaluate_pipeline(
    df_1m: pd.DataFrame,
    weights: dict[str, float] | None = None,
    min_score: float = 70.0,
    require_liquidity_sweep: bool = False,
    require_retest: bool = False,
    news_score: float = 100.0,
) -> PipelineDecision:
    """Evaluate only completed market data; never places an order.

    The function is deliberately deterministic. AI/model scores can be supplied by
    a higher layer, but cannot bypass this pipeline or the risk/execution gates.
    """
    if not 0 <= min_score <= 100:
        raise ValueError("min_score must be between 0 and 100")
    if not 0 <= news_score <= 100:
        raise ValueError("news_score must be between 0 and 100")

    mtf = build_mtf(df_1m)
    if min(len(mtf["15m"]), len(mtf["5m"]), len(mtf["1m"])) < 30:
        return PipelineDecision(False, "data", 0.0, "no_trade", "insufficient multi-timeframe history")

    f15, f5, f1 = mtf["15m"], mtf["5m"], mtf["1m"]
    e15_fast, e15_slow = ema(f15.close, 20).iloc[-1], ema(f15.close, 50).iloc[-1]
    direction = "buy" if e15_fast > e15_slow else "sell"

    e5_fast, e5_slow = ema(f5.close, 20).iloc[-1], ema(f5.close, 50).iloc[-1]
    confirmation = "buy" if e5_fast > e5_slow else "sell"
    if confirmation != direction:
        return PipelineDecision(False, "5m_confirmation", 0.0, "no_trade", "5M disagrees with 15M direction")

    structure = detect_structure(f5)
    expected_trend = "bullish" if direction == "buy" else "bearish"
    structure_ok = structure.trend == expected_trend
    liquidity = analyze_liquidity(f5)
    sweep_ok = liquidity.sweep in {"sell_side_sweep" if direction == "buy" else "buy_side_sweep"}
    if require_liquidity_sweep and not sweep_ok:
        return PipelineDecision(False, "liquidity_sweep", 0.0, "no_trade", "required directional liquidity sweep not detected")
    if require_retest and not structure.retest:
        return PipelineDecision(False, "retest", 0.0, "no_trade", "required structure retest not detected")

    rsi_value = float(rsi(f1.close).iloc[-1])
    atr_value = float(atr(f1, 14).iloc[-1])
    adx_value = float(adx(f5, 14).iloc[-1])
    price = float(f1.close.iloc[-1])
    if not all(pd.notna(v) for v in (rsi_value, atr_value, adx_value, price)) or atr_value <= 0:
        return PipelineDecision(False, "indicators", 0.0, "no_trade", "invalid indicator state")

    momentum_ok = (direction == "buy" and rsi_value >= 50) or (direction == "sell" and rsi_value <= 50)
    atr_baseline = float(atr(f1, 14).rolling(50).median().iloc[-1])
    volatility_ok = pd.notna(atr_baseline) and 0.5 * atr_baseline <= atr_value <= 2.5 * atr_baseline
    components: dict[str, float] = {
        "trend": 100.0 if direction == confirmation else 0.0,
        "momentum": 85.0 if momentum_ok else 35.0,
        "structure": 90.0 if structure_ok else 45.0,
        "liquidity": 95.0 if sweep_ok else 55.0,
        "volatility": 85.0 if volatility_ok else 35.0,
        "session": _session_score(f1),
        "news": news_score,
    }
    score = score_signal(components, weights)
    if score.total < min_score:
        return PipelineDecision(False, "ai_score", score.total, score.verdict, "score below execution threshold")
    return PipelineDecision(True, "risk_gate", score.total, score.verdict, f"{direction} setup passed signal pipeline")
