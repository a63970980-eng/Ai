from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from forex_robot.ai.providers import build_ai_engine
from forex_robot.ai.council import run_council
from forex_robot.ai.registry import ModelRegistry
from forex_robot.ai.ledger import ledger
from forex_robot.agents.orchestrator import TradingAgentOrchestrator
from forex_robot.analytics import analytics
from forex_robot.backtest.engine import run_backtest
from forex_robot.backtest.exits import BacktestExitConfig
from forex_robot.domain.models import PositionSizeRequest, PositionSizeResponse, Signal
from forex_robot.domain.trading import AccountState, OrderRequest
from forex_robot.execution.broker import PaperBroker
from forex_robot.market.providers import build_market_feed
from forex_robot.journal import Journal, TradeJournalEntry
from forex_robot.portfolio.risk import PortfolioRiskLimits, evaluate_portfolio
from forex_robot.pipeline import evaluate_pipeline
from forex_robot.regime.detector import Regime, detect_regime
from forex_robot.research.validation import monte_carlo_bootstrap, walk_forward_windows
from forex_robot.observability import metrics
from forex_robot.risk.manager import RiskManager
from forex_robot.robustness.stress import stress_returns
from forex_robot.scoring import score_signal
from forex_robot.settings import settings
from forex_robot.strategies.scalping import breakout, liquidity, mean_reversion, momentum, scalping, trend

app = FastAPI(title="AI Crypto Quant Trading Platform", version="1.6.0", docs_url="/docs")
risk_manager = RiskManager()
paper_broker = PaperBroker()
journal = Journal()
ai_engine, ai_provider = build_ai_engine()
market_feed = build_market_feed()
started = datetime.now(timezone.utc)
ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


class ScoreRequest(BaseModel):
    components: dict[str, float]
    weights: dict[str, float] | None = None


class MarketRequest(BaseModel):
    symbol: str
    candles: list[dict] = Field(default_factory=list)


class AIScoreRequest(BaseModel):
    signal: Signal
    regime: Regime = Regime.UNKNOWN


class RiskGateRequest(BaseModel):
    signal: Signal
    spread: float = Field(ge=0)
    slippage: float = Field(default=0.0, ge=0)
    proposed_risk: float = Field(default=0.0, ge=0)
    equity: float = Field(default=100_000.0, gt=0)
    day_start_equity: float = Field(default=100_000.0, gt=0)
    peak_equity: float = Field(default=100_000.0, gt=0)
    open_positions: int = Field(default=0, ge=0)
    consecutive_losses: int = Field(default=0, ge=0)
    portfolio_risk: float = Field(default=0.0, ge=0)
    kill_switch: bool = False
    currency_exposure: dict[str, float] = Field(default_factory=dict)


class PaperExecuteRequest(BaseModel):
    signal: Signal
    spread: float = Field(ge=0)
    proposed_risk: float = Field(default=0.0, ge=0)
    equity: float = Field(default=100_000.0, gt=0)
    day_start_equity: float = Field(default=100_000.0, gt=0)
    peak_equity: float = Field(default=100_000.0, gt=0)
    consecutive_losses: int = Field(default=0, ge=0)
    portfolio_risk: float = Field(default=0.0, ge=0)
    kill_switch: bool = False
    currency_exposure: dict[str, float] = Field(default_factory=dict)


class BacktestRequest(MarketRequest):
    strategy: str = "momentum"
    spread: float = Field(default=0.0, ge=0)
    slippage: float = Field(default=0.0, ge=0)
    fee: float = Field(default=0.0, ge=0)
    risk_per_trade: float = Field(default=1.0, gt=0, le=1)
    execution_delay: int = Field(default=0, ge=0)
    account_equity: float = Field(default=100_000.0, gt=0)
    take_profit_multiples: list[float] | None = None
    partial_exit_fractions: list[float] | None = None
    break_even_after_r: float | None = 1.0
    trailing_atr_multiple: float | None = 1.5


class ResearchValidationRequest(BaseModel):
    returns: list[float]
    simulations: int = Field(default=2000, ge=100, le=100000)
    seed: int = Field(default=42)


class WalkForwardRequest(BaseModel):
    length: int = Field(gt=0)
    train_size: int = Field(gt=0)
    test_size: int = Field(gt=0)
    step: int | None = Field(default=None, gt=0)


class StressRequest(BaseModel):
    returns: list[float]
    spread_factor: float = Field(default=1.5, gt=0)
    slippage_factor: float = Field(default=1.5, gt=0)
    volatility_factor: float = Field(default=1.0, gt=0)


STRATEGIES = {
    "momentum": momentum,
    "scalping": scalping,
    "mean_reversion": mean_reversion,
    "breakout": breakout,
    "trend": trend,
    "liquidity": liquidity,
}


@app.get("/")
def dashboard():
    p = FRONTEND / "index.html"
    return FileResponse(p) if p.exists() else {"service": "AI Crypto Quant Trading Platform", "docs": "/docs"}


@app.get("/styles.css")
def styles():
    return FileResponse(FRONTEND / "styles.css")


@app.get("/app.js")
def script():
    return FileResponse(FRONTEND / "app.js")


@app.get("/api/v1/health")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-forex-trading-platform",
        "environment": settings.environment,
        "live_trading": settings.live_trading_enabled,
        "paper_trading": settings.paper_trading_enabled,
        "ai_provider": ai_provider,
        "market_feed": getattr(market_feed, "provider_name", market_feed.__class__.__name__.replace("MarketData", "").lower()) if market_feed else "not_configured",
        "uptime_since": started.isoformat(),
    }


@app.get("/api/v1/settings")
def get_settings():
    return {
        "environment": settings.environment,
        "live_trading_enabled": settings.live_trading_enabled,
        "paper_trading_enabled": settings.paper_trading_enabled,
        "risk_per_trade": settings.max_risk_per_trade,
        "daily_loss": settings.max_daily_loss,
        "drawdown": settings.max_drawdown,
        "max_open_positions": settings.max_open_positions,
        "supported_strategies": list(STRATEGIES),
        "ai_provider": ai_provider,
        "market_feed": "binance" if market_feed else "not_configured",
    }


@app.post("/api/v1/risk/position-size", response_model=PositionSizeResponse)
@app.post("/risk/position-size", response_model=PositionSizeResponse)
def position_size(request: PositionSizeRequest):
    try:
        return risk_manager.position_size(request)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def _risk_decision(request: RiskGateRequest | PaperExecuteRequest):
    account_state = AccountState(
        equity=request.equity,
        day_start_equity=request.day_start_equity,
        peak_equity=request.peak_equity,
        open_positions=len(paper_broker.positions()),
        consecutive_losses=request.consecutive_losses,
        portfolio_risk=request.portfolio_risk,
        kill_switch=request.kill_switch,
        currency_exposure=request.currency_exposure,
    )
    limits = PortfolioRiskLimits(
        max_daily_loss_fraction=settings.max_daily_loss,
        max_drawdown_fraction=settings.max_drawdown,
        max_open_positions=settings.max_open_positions,
        max_spread=settings.max_spread_pips * 0.0001,
        max_slippage=settings.max_slippage_pips * 0.0001,
        min_signal_confidence=settings.min_signal_confidence,
    )
    return evaluate_portfolio(
        account_state, request.signal, request.spread, limits=limits,
        proposed_risk=request.proposed_risk, slippage=getattr(request, "slippage", 0.0),
    )


@app.post("/api/v1/risk/evaluate")
def evaluate_risk(request: RiskGateRequest):
    decision = _risk_decision(request)
    return {"allowed": decision.allowed, "reason": decision.reason}


@app.post("/api/v1/signals/score")
def signal_score(request: ScoreRequest):
    return score_signal(request.components, request.weights).__dict__


@app.post("/api/v1/ai/score")
def ai_score(request: AIScoreRequest):
    try:
        result = ai_engine.score(request.signal, request.regime)
        return {
            "score": result.model_score,
            "confidence": result.signal.confidence if result.signal else 0.0,
            "regime": result.regime.value,
            "explanation": result.explanation,
            "model": result.model_name if result.model_name else ai_provider,
            "provider": ai_provider,
            "risk_authority": "risk_engine",
        }
    except Exception as exc:
        raise HTTPException(503, "AI provider unavailable; no trade decision was made") from exc


@app.get("/api/v1/signals")
def signals():
    return {"signals": [], "source": "use /api/v1/signals/live when market feed is configured", "ai_provider": ai_provider}


@app.get("/api/v1/signals/live")
def live_signal(
    symbol: str = Query(default="BTCUSDT", min_length=5, max_length=20),
    strategy: str = Query(default="momentum"),
    granularity: str = Query(default="15m", pattern=r"^(1m|3m|5m|15m|30m|1h|2h|4h|1d)$"),
    count: int = Query(default=500, ge=30, le=1000),
):
    if market_feed is None:
        raise HTTPException(503, "market feed unavailable")
    strategy_fn = STRATEGIES.get(strategy)
    if strategy_fn is None:
        raise HTTPException(422, f"unsupported strategy; available: {', '.join(STRATEGIES)}")
    try:
        feed = market_feed.candles(symbol, granularity, count)
    except Exception as exc:
        raise HTTPException(502, "market data provider unavailable") from exc
    if len(feed.candles) < 30:
        return {"status": "no_signal", "reason": "insufficient_complete_candles", "candles": len(feed.candles)}
    candidate = strategy_fn(symbol, feed.candles)
    regime = detect_regime(feed.candles) if len(feed.candles) >= 60 else Regime.UNKNOWN
    if candidate is None:
        return {"status": "no_signal", "symbol": symbol, "strategy": strategy, "regime": regime.value, "candles": len(feed.candles)}
    try:
        ai = ai_engine.score(candidate, regime)
    except Exception as exc:
        raise HTTPException(503, "AI provider unavailable; no trade decision was made") from exc
    risk_request = RiskGateRequest(
        signal=ai.signal or candidate,
        spread=0.0,
        proposed_risk=settings.max_risk_per_trade,
        equity=paper_broker.account()["equity"],
        day_start_equity=paper_broker.account()["equity"],
        peak_equity=paper_broker.account()["equity"],
    )
    decision = _risk_decision(risk_request)
    return {
        "status": "valid" if decision.allowed and ai.model_score >= settings.min_signal_confidence else "blocked",
        "symbol": symbol,
        "strategy": strategy,
        "provider": feed.provider,
        "granularity": granularity,
        "candles": len(feed.candles),
        "regime": regime.value,
        "signal": ai.signal.model_dump(mode="json") if ai.signal else None,
        "ai_score": ai.model_score,
        "ai_explanation": ai.explanation,
        "risk_allowed": decision.allowed,
        "risk_reason": decision.reason,
        "execution_mode": "paper_only",
        "live_trading_enabled": settings.live_trading_enabled,
    }


@app.post("/api/v1/paper/execute")
def paper_execute(request: PaperExecuteRequest):
    if not settings.paper_trading_enabled:
        raise HTTPException(403, "paper trading is disabled")
    if settings.live_trading_enabled:
        raise HTTPException(403, "live mode cannot be used through the paper endpoint")
    decision = _risk_decision(request)
    if not decision.allowed:
        return {"executed": False, "reason": decision.reason, "mode": "paper"}
    order = OrderRequest(
        symbol=request.signal.symbol,
        side=request.signal.side.value if hasattr(request.signal.side, "value") else str(request.signal.side),
        units=1.0,
        entry=request.signal.entry,
        stop_loss=request.signal.stop_loss,
        take_profit=request.signal.take_profit,
        client_order_id=f"PAPER-{request.signal.symbol}-{int(request.signal.timestamp.timestamp())}",
    )
    try:
        order_id = paper_broker.place(order)
        journal.record(
            TradeJournalEntry(
                timestamp=request.signal.timestamp,
                pair=request.signal.symbol,
                direction=request.signal.side.value,
                entry=request.signal.entry,
                stop_loss=request.signal.stop_loss,
                take_profit=request.signal.take_profit,
                units=order.units,
                risk=request.proposed_risk or settings.max_risk_per_trade,
                signal_score=request.signal.confidence,
                strategy="paper",
                regime="unknown",
                session="unknown",
                spread=request.spread,
                slippage=0.0,
                ai_analysis=request.signal.reason,
            )
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"executed": True, "mode": "paper", "order_id": order_id, "signal": request.signal.model_dump(mode="json")}


class PipelineRequest(BaseModel):
    candles: list[dict] = Field(default_factory=list)
    symbol: str | None = None
    min_score: float = Field(default=70.0, ge=0, le=100)
    require_liquidity_sweep: bool = False
    require_retest: bool = False


@app.post("/api/v1/pipeline/evaluate")
def pipeline_evaluate(request: PipelineRequest):
    """Run the deterministic research pipeline without placing an order."""
    if len(request.candles) < 30:
        raise HTTPException(422, "at least 30 candles required")
    df = pd.DataFrame(request.candles)
    required = {"open", "high", "low", "close"}
    if not required.issubset(df.columns):
        raise HTTPException(422, "OHLC columns required")
    try:
        result = evaluate_pipeline(
            df,
            min_score=request.min_score,
            require_liquidity_sweep=request.require_liquidity_sweep,
            require_retest=request.require_retest,
            symbol=request.symbol,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return result.__dict__


@app.get("/api/v1/diagnostics")
def diagnostics():
    """Expose deployment/runtime diagnostics without secrets."""
    return {
        "api": "ready",
        "environment": settings.environment,
        "paper_trading": settings.paper_trading_enabled,
        "live_trading": settings.live_trading_enabled,
        "live_gate": "closed" if not settings.live_trading_enabled else "configured",
        "ai_provider": ai_provider,
        "market_feed_configured": market_feed is not None,
        "database": "sqlite_journal",
        "vercel_entrypoint": "api.py",
    }


@app.post("/api/v1/market")
def market(request: MarketRequest):
    if not request.candles:
        return {"symbol": request.symbol, "candles": 0}
    df = pd.DataFrame(request.candles)
    regime = detect_regime(df) if len(df) >= 60 and {"open", "high", "low", "close"}.issubset(df.columns) else Regime.UNKNOWN
    return {"symbol": request.symbol, "candles": len(df), "regime": regime.value, "last": df.iloc[-1].to_dict()}


@app.get("/api/v1/account")
def account():
    state = paper_broker.account()
    return {**state, "mode": "paper", "live_enabled": settings.live_trading_enabled}


@app.get("/api/v1/positions")
def positions():
    return {"positions": [p.__dict__ for p in paper_broker.positions()], "mode": "paper"}


@app.get("/api/v1/trades")
def trades(limit: int = Query(default=100, ge=1, le=5000)):
    return {"trades": journal.all(limit), "source": "sqlite_journal"}


@app.get("/api/v1/journal")
def journal_entries(limit: int = Query(default=100, ge=1, le=5000)):
    return {"entries": journal.all(limit), "source": "sqlite_journal"}


@app.post("/api/v1/analytics")
def analytics_endpoint(returns: list[float]):
    try:
        return analytics(returns)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/research/monte-carlo")
def research_monte_carlo(request: ResearchValidationRequest):
    try:
        return monte_carlo_bootstrap(request.returns, request.simulations, request.seed).__dict__
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/research/walk-forward")
def research_walk_forward(request: WalkForwardRequest):
    try:
        windows = walk_forward_windows(request.length, request.train_size, request.test_size, request.step)
        return {"windows": [w.__dict__ for w in windows], "count": len(windows)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/v1/observability")
def observability():
    return metrics.snapshot().__dict__


@app.get("/api/v1/ai/models")
def ai_models():
    registry = ModelRegistry()
    return {
        "models": [profile.__dict__ for profile in registry.profiles()],
        "configured_from_environment": bool(__import__("os").getenv("AI_COUNCIL_MODELS")),
        "execution": "disabled",
        "risk_authority": "risk_engine",
    }


@app.post("/api/v1/ai/council")
def ai_council(request: AIScoreRequest):
    """Run all configured AI council members, then return consensus only.

    This endpoint never places orders. Deterministic risk controls remain
    authoritative outside the model council.
    """
    result = run_council(request.signal, request.regime)
    evaluation_id = uuid4().hex
    ledger.record(evaluation_id, request.signal, result.opinions)
    return {
        "evaluation_id": evaluation_id,
        "consensus_score": result.consensus_score,
        "agreement": result.agreement,
        "stance": result.stance,
        "conflicts": result.conflicts,
        "successful_models": result.successful_models,
        "failed_models": result.failed_models,
        "opinions": [op.__dict__ for op in result.opinions],
        "risk_authority": "risk_engine",
        "execution": "disabled",
    }


@app.get("/api/v1/ai/performance")
def ai_performance():
    """Return observed model performance from settled council evaluations."""
    return {"models": ledger.performance()}


class AIOutcomeRequest(BaseModel):
    evaluation_id: str = Field(min_length=8, max_length=128)
    outcome: float = Field(ge=-1, le=1)


@app.post("/api/v1/ai/outcomes/settle")
def settle_ai_outcome(request: AIOutcomeRequest):
    try:
        updated = ledger.settle(request.evaluation_id, request.outcome)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if updated == 0:
        raise HTTPException(404, "evaluation not found or already settled")
    return {"evaluation_id": request.evaluation_id, "settled_rows": updated}


@app.get("/api/v1/ai/evaluations/{evaluation_id}")
def ai_evaluation(evaluation_id: str):
    rows = ledger.get(evaluation_id)
    if not rows:
        raise HTTPException(404, "evaluation not found")
    return {"evaluation_id": evaluation_id, "opinions": rows}


@app.post("/api/v1/ai/agents")
def ai_agents(request: AIScoreRequest):
    """Run analyst -> planner -> risk monitor without broker execution."""
    council = run_council(request.signal, request.regime)
    decision = TradingAgentOrchestrator.from_council(council).evaluate({})
    return {
        "analysis": decision.analysis.payload,
        "execution_plan": decision.execution_plan.payload,
        "risk": decision.risk.payload,
        "execution": "disabled",
        "risk_authority": "risk_engine",
    }


@app.post("/api/v1/stress")
def stress(request: StressRequest):
    try:
        return stress_returns(request.returns, request.spread_factor, request.slippage_factor, request.volatility_factor).__dict__
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/backtest")
def backtest(request: BacktestRequest):
    if len(request.candles) < 3:
        raise HTTPException(422, "at least 3 candles required")
    strategy_fn = STRATEGIES.get(request.strategy)
    if strategy_fn is None:
        raise HTTPException(422, f"unsupported strategy; available: {', '.join(STRATEGIES)}")
    df = pd.DataFrame(request.candles)
    if not {"open", "high", "low", "close"}.issubset(df.columns):
        raise HTTPException(422, "OHLC columns required")
    exit_config = None
    if request.take_profit_multiples is not None or request.partial_exit_fractions is not None:
        multiples = tuple(request.take_profit_multiples or (1.0, 1.5, 2.0, 3.0))
        fractions = tuple(request.partial_exit_fractions or (0.25, 0.25, 0.25, 0.25))
        try:
            exit_config = BacktestExitConfig(multiples, fractions, request.break_even_after_r, request.trailing_atr_multiple)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    result = run_backtest(
        df, lambda history: strategy_fn(request.symbol, history), spread=request.spread,
        slippage=request.slippage, fee=request.fee, risk_per_trade=request.risk_per_trade,
        execution_delay=request.execution_delay, account_equity=request.account_equity,
        exit_config=exit_config,
    )
    return result.__dict__


@app.get("/api/v1/risk")
def risk():
    return {
        "live_trading": settings.live_trading_enabled,
        "max_risk_per_trade": settings.max_risk_per_trade,
        "max_daily_loss": settings.max_daily_loss,
        "max_drawdown": settings.max_drawdown,
        "max_open_positions": settings.max_open_positions,
        "max_spread_fraction": settings.max_spread_fraction,
        "max_slippage_fraction": settings.max_slippage_fraction,
        "min_signal_confidence": settings.min_signal_confidence,
    }
