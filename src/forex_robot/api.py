from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from forex_robot.analytics import analytics
from forex_robot.backtest.engine import run_backtest
from forex_robot.backtest.exits import BacktestExitConfig
from forex_robot.domain.models import PositionSizeRequest, PositionSizeResponse, Signal
from forex_robot.domain.trading import AccountState
from forex_robot.execution.broker import PaperBroker
from forex_robot.portfolio.risk import PortfolioRiskLimits, evaluate_portfolio
from forex_robot.risk.manager import RiskManager
from forex_robot.robustness.stress import stress_returns
from forex_robot.scoring import score_signal
from forex_robot.settings import settings
from forex_robot.strategies.scalping import breakout, liquidity, mean_reversion, momentum, scalping, trend

app = FastAPI(title="AI Forex Trading Platform", version="1.4.0", docs_url="/docs")
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
    account_equity: float = Field(default=100_000.0, gt=0)
    take_profit_multiples: list[float] | None = None
    partial_exit_fractions: list[float] | None = None
    break_even_after_r: float | None = 1.0
    trailing_atr_multiple: float | None = 1.5


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
        "supported_strategies": list(STRATEGIES),
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
    decision = evaluate_portfolio(account_state, request.signal, request.spread, limits=limits,
                                  proposed_risk=request.proposed_risk, slippage=request.slippage)
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


@app.post("/api/v1/stress")
def stress(request: StressRequest):
    try:
        return stress_returns(request.returns, request.spread_factor, request.slippage_factor,
                              request.volatility_factor).__dict__
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
            exit_config = BacktestExitConfig(multiples, fractions, request.break_even_after_r,
                                             request.trailing_atr_multiple)
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
        "max_spread_pips": settings.max_spread_pips,
        "max_slippage_pips": settings.max_slippage_pips,
        "min_signal_confidence": settings.min_signal_confidence,
    }
