from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from forex_robot.analytics import analytics
from forex_robot.backtest.engine import run_backtest
from forex_robot.domain.models import PositionSizeRequest, PositionSizeResponse, Signal
from forex_robot.domain.trading import AccountState
from forex_robot.execution.broker import PaperBroker
from forex_robot.portfolio.risk import PortfolioRiskLimits, evaluate_portfolio
from forex_robot.risk.manager import RiskManager
from forex_robot.scoring import score_signal
from forex_robot.settings import settings
from forex_robot.strategies.scalping import breakout, liquidity, mean_reversion, momentum, scalping, trend

app = FastAPI(title="AI Forex Trading Platform", version="1.3.0", docs_url="/docs")
risk_manager = RiskManager()
paper_broker = PaperBroker()
started = datetime.now(timezone.utc)
ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


class ScoreRequest(BaseModel):
    components: dict[str, float]
    weights: dict[str, float] | None = None


class MarketRequest(BaseModel):
    symbol: str
    candles: list[dict] = Field(default_factory=list)


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


class BacktestRequest(MarketRequest):
    strategy: str = "momentum"
    spread: float = Field(default=0.0, ge=0)
    slippage: float = Field(default=0.0, ge=0)
    fee: float = Field(default=0.0, ge=0)
    risk_per_trade: float = Field(default=1.0, gt=0, le=1)
    execution_delay: int = Field(default=0, ge=0)


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
    return FileResponse(p) if p.exists() else {"service": "AI Forex Trading Platform", "docs": "/docs"}


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
    }


@app.post("/api/v1/risk/position-size", response_model=PositionSizeResponse)
@app.post("/risk/position-size", response_model=PositionSizeResponse)
def position_size(request: PositionSizeRequest):
    try:
        return risk_manager.position_size(request)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/risk/evaluate")
def evaluate_risk(request: RiskGateRequest):
    account_state = AccountState(
        equity=request.equity,
        day_start_equity=request.day_start_equity,
        peak_equity=request.peak_equity,
        open_positions=request.open_positions,
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
    decision = evaluate_portfolio(
        account_state,
        request.signal,
        request.spread,
        limits=limits,
        proposed_risk=request.proposed_risk,
        slippage=request.slippage,
    )
    return {"allowed": decision.allowed, "reason": decision.reason}


@app.post("/api/v1/signals/score")
def signal_score(request: ScoreRequest):
    return score_signal(request.components, request.weights).__dict__


@app.get("/api/v1/signals")
def signals():
    return {"signals": [], "source": "no_market_feed_configured"}


@app.post("/api/v1/market")
def market(request: MarketRequest):
    if not request.candles:
        return {"symbol": request.symbol, "candles": 0}
    df = pd.DataFrame(request.candles)
    return {"symbol": request.symbol, "candles": len(df), "last": df.iloc[-1].to_dict()}


@app.get("/api/v1/account")
def account():
    state = paper_broker.account()
    return {**state, "mode": "paper", "live_enabled": settings.live_trading_enabled}


@app.get("/api/v1/positions")
def positions():
    return {"positions": [p.__dict__ for p in paper_broker.positions()], "mode": "paper"}


@app.get("/api/v1/trades")
def trades():
    return {"trades": [], "source": "journal_storage_not_configured"}


@app.get("/api/v1/journal")
def journal():
    return {"entries": [], "source": "journal_storage_not_configured"}


@app.post("/api/v1/analytics")
def analytics_endpoint(returns: list[float]):
    try:
        return analytics(returns)
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
    result = run_backtest(
        df,
        lambda history: strategy_fn(request.symbol, history),
        spread=request.spread,
        slippage=request.slippage,
        fee=request.fee,
        risk_per_trade=request.risk_per_trade,
        execution_delay=request.execution_delay,
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
        "max_spread_pips": settings.max_spread_pips,
        "max_slippage_pips": settings.max_slippage_pips,
        "min_signal_confidence": settings.min_signal_confidence,
    }
