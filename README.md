# AI Forex Scalping & Quantitative Trading Platform

Research-oriented, safety-first Forex research and paper-trading platform. The repository separates market data, deterministic analytics, signal scoring, portfolio risk, execution boundaries, backtesting and observability so model output cannot override safety controls.

## Safety contract

- `LIVE_TRADING_ENABLED=false` by default.
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
- Session and high-impact news blocking interfaces
- Scalping, trend, momentum and liquidity strategy primitives plus ensemble/scoring boundary
- Configurable 0–100 score with Trend/Momentum/Structure/Liquidity/Volatility/Session/News weights
- Portfolio risk gate: daily loss, drawdown, open positions, portfolio risk, consecutive losses, spread and emergency kill switch
- Broker abstraction with PaperBroker and explicit MT5/OANDA/cTrader boundaries
- Backtesting with next-bar execution, spread/slippage/fees and SL/TP evaluation
- Walk-forward splits, Monte Carlo robustness and stress scenarios
- Trade journal and performance analytics
- FastAPI `/api/v1/*` surface and integrated responsive terminal dashboard
- PostgreSQL schema for users, accounts, instruments, market data, signals, trades, orders, positions, strategies, risk, news, backtests, predictions and audit events
- Docker + PostgreSQL compose stack and CI lint/test/compile workflow

## Architecture

`Market Data → Validation → MTF → Features → Regime → Structure/Liquidity → Strategies → Ensemble → AI/Statistical Scoring → Portfolio Risk → Execution → Monitoring → Journal/Analytics`

## Run

```bash
python -m pip install -e '.[dev]'
uvicorn forex_robot.api:app --reload
pytest
ruff check .
docker compose up --build
```

Real broker SDKs, credentials and live feeds are deliberately not fabricated. Configure them in deployment infrastructure only after independent paper/forward validation and operational approval. No profitability guarantee is made.
