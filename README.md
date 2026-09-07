# AI Forex Scalping & Quantitative Trading Platform

Research-oriented, safety-first Forex research and paper-trading platform. The repository separates market data, deterministic analytics, signal scoring, portfolio risk, execution boundaries, backtesting and observability so model output cannot override safety controls.

## Safety contract

- `LIVE_TRADING_ENABLED=false` by default.
- Live trading additionally requires `ENVIRONMENT=production`.
- Paper/backtest modes are isolated from live mode.
- No Martingale and no averaging-down recovery logic.
- Risk controls have final authority over model or strategy output.
- Credentials are environment/secrets only; never commit broker keys.
- No fabricated live prices, fills, performance, or profitability claims.
- Live broker integration remains disabled until credentials, broker-specific testing, operational monitoring and independent validation are completed.

## Implemented layers

- UTC market-data validation and 1M/5M/15M resampling
- EMA20/50/200, RSI14, MACD, ADX14, ATR14, Bollinger, VWAP and volatility features
- Market structure: swings, HH/HL/LH/LL and BOS-style events
- Liquidity: buy/sell-side pools, equal highs/lows, sweeps and FVG/imbalance detection
- Session and pair-aware high-impact news blocking interfaces
- Scalping, trend, momentum and liquidity strategy primitives plus ensemble/scoring boundary
- Configurable 0–100 score with Trend/Momentum/Structure/Liquidity/Volatility/Session/News weights
- Portfolio risk gate: daily loss, drawdown, open positions, portfolio risk, consecutive losses, spread, currency exposure and emergency kill switch
- Broker abstraction with PaperBroker and explicit MT5/OANDA/cTrader boundaries
- Backtesting with next-bar execution, spread/slippage/fees and SL/TP evaluation
- Walk-forward evaluation and out-of-sample windows
- Monte Carlo robustness including drawdown, losing streak and risk-of-ruin estimates
- Trade journal and performance analytics including win/loss averages and streaks
- FastAPI `/api/v1/*` surface and integrated responsive terminal dashboard
- PostgreSQL schema for users, accounts, instruments, market data, signals, trades, orders, positions, strategies, risk, news, backtests, predictions and audit events
- Docker + PostgreSQL compose stack with externally supplied database credentials
- CI lint/type-check/test/compile workflow

## Architecture

`Market Data → Validation → MTF → Features → Regime → Structure/Liquidity → Strategies → Ensemble → AI/Statistical Scoring → Portfolio Risk → Execution → Monitoring → Journal/Analytics`

## Run locally

```bash
python -m pip install -e '.[dev]'
uvicorn forex_robot.api:app --reload
pytest
ruff check . --select E9,F63,F7,F82
mypy src
```

## Docker

Set `POSTGRES_PASSWORD` in the deployment environment (never commit the real value), then run:

```bash
docker compose up --build
```

## Production gate

Before any live broker connection: complete broker adapter certification, paper/forward validation, out-of-sample and walk-forward testing, stress testing, reconciliation/idempotency testing, monitoring/alerting, credential/secrets configuration, and an explicit operational approval. A passing CI build is necessary but is not evidence of profitability or live-trading readiness.

Real broker SDKs, credentials and live feeds are deliberately not fabricated. No profitability guarantee is made.
