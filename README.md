# AI Forex Scalping & Quantitative Trading Platform

A safety-first quantitative Forex research and paper-trading platform. Deterministic market, strategy and risk controls remain authoritative over AI reasoning and broker execution.

## Safety contract

- `LIVE_TRADING_ENABLED=false` by default.
- Live trading additionally requires `ENVIRONMENT=production`.
- Paper and backtest modes are isolated from live execution.
- No Martingale or averaging-down recovery logic.
- Risk controls have final authority over model output.
- Credentials belong in Vercel/secret-manager environment variables, never Git.
- No fabricated live prices, fills, performance or profitability claims.
- MT5/OANDA/cTrader adapters are explicit boundaries until broker-specific certification is completed.

## Implemented platform

- UTC data validation and 1M/5M/15M multi-timeframe resampling
- EMA20/50/200, RSI14, MACD, ADX14, ATR14, Bollinger, VWAP and volatility features
- Market structure: swings, HH/HL/LH/LL and BOS-style events
- Liquidity: buy/sell-side pools, equal highs/lows, sweeps and FVG/imbalance detection
- Session handling and pair-aware high-impact news blocking interface
- Six strategy primitives: scalping, momentum, trend, breakout, mean reversion and liquidity
- Weighted 0–100 signal score with Trend/Momentum/Structure/Liquidity/Volatility/Session/News components
- Portfolio risk gate: daily loss, drawdown, open positions, portfolio risk, consecutive losses, spread, slippage, currency exposure and kill switch
- Paper broker with idempotent client order IDs and order-geometry validation
- Backtesting with next-bar execution, spread/slippage/fees and risk-based position sizing
- Dynamic backtest exits: multiple TP levels, partial exits, break-even and ATR trailing
- Walk-forward validation and out-of-sample windows
- Monte Carlo robustness plus deterministic spread/slippage/volatility stress testing
- Market-feed corruption checks for missing OHLC, invalid values and duplicate timestamps
- Execution reconciliation and connection-health boundaries
- FastAPI `/api/v1/*` surface for health, settings, scoring, risk, backtesting, analytics and stress analysis
- Responsive dark quantitative terminal dashboard
- PostgreSQL schema covering accounts, instruments, market data, signals, orders, positions, trades, strategies, risk, news, backtests, predictions and audit events
- Docker Compose with PostgreSQL and a container healthcheck
- CI: dependency installation, Ruff correctness checks, mypy, pytest and compile validation

## Architecture

`Market Data → Validation → MTF → Features → Regime → Structure/Liquidity → Strategies → Ensemble/AI → Signal Score → Portfolio Risk → Execution → Monitoring → Journal/Analytics`

## Local run

```bash
python -m pip install -e '.[dev]'
uvicorn forex_robot.api:app --reload
pytest -q
ruff check . --select E9,F63,F7,F82
mypy src
```

## Docker

Set a real `POSTGRES_PASSWORD` outside Git, then:

```bash
docker compose up --build
```

The API listens on port `8000`; the terminal is served from `/`.

## AI providers

`OPENROUTER_API_KEY` and `GEMINI_API_KEY` are supported as deployment secrets for future/provider-specific AI reasoning. They are intentionally absent from source control and do not authorize live trading by themselves.

## Release gate

The current release target is **research/paper-trading production**, not unattended live-money trading. The live gate remains closed until the following are independently completed:

1. Real market-feed integration and data-quality monitoring.
2. Broker-specific adapter implementation and certification.
3. Forward/paper validation and reconciliation tests.
4. Walk-forward and out-of-sample evaluation on representative data.
5. Stress, Monte Carlo and failure-injection validation.
6. Persistent journal/database wiring in the deployed runtime.
7. Production monitoring, alerting and audit retention.
8. Secrets, access control and operational approval.
9. Only then: controlled live enablement with small limits and an emergency stop.

A green CI run proves software checks pass; it does **not** prove profitability or live-trading readiness.
