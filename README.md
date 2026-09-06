# AI Forex Trading Robot

Research-oriented, safety-first Forex research and paper-trading platform. The repository separates market data, deterministic analytics, signal scoring, portfolio risk, execution boundaries, backtesting and observability so that model output can never override safety controls.

## Safety contract

- `LIVE_TRADING_ENABLED=false` by default.
- Paper/backtest modes are isolated from live mode.
- No Martingale and no averaging-down recovery logic.
- Risk controls have final authority over model or strategy output.
- Credentials are environment/secrets only; never commit broker keys.
- No fabricated live prices, fills, performance, or profitability claims.
- Any live broker integration remains disabled until credentials, broker-specific testing, operational monitoring and independent validation are completed.

## Architecture

`Market Data → Validation → MTF → Features → Regime → Structure/Liquidity → Strategies → Ensemble → AI/Statistical Scoring → Portfolio Risk → Execution Boundary → Monitoring → Journal/Analytics`

### MTF model

The research pipeline supports a 15-minute context, 5-minute confirmation and 1-minute execution-analysis layer. Resampling is timestamp-aware and uses only information available at or before the evaluated bar.

### Signal scoring

The configurable baseline is: Trend 20, Momentum 15, Structure 20, Liquidity 15, Volatility 10, Session 10, News 10. Verdict bands are `NO_TRADE <60`, `WATCH 60–69`, `VALID 70–79`, `STRONG 80–89`, `PREMIUM 90–100`.

## Repository layout

- `src/forex_robot/domain` — typed trading contracts
- `src/forex_robot/market` — validation, sessions and multi-timeframe data
- `src/forex_robot/features` — deterministic quantitative features
- `src/forex_robot/regime` — market-state classification
- `src/forex_robot/strategies` — strategy implementations
- `src/forex_robot/ai` — model boundary; never the final risk authority
- `src/forex_robot/scoring.py` — explainable weighted signal score
- `src/forex_robot/risk` and `portfolio` — deterministic safety controls
- `src/forex_robot/backtest` — historical research path
- `src/forex_robot/robustness` — robustness/stress research
- `src/forex_robot/execution` — broker boundary and paper execution

## Development

```bash
python -m pip install -e '.[dev]'
uvicorn forex_robot.api:app --reload
pytest
ruff check .
```

A production deployment must add broker-specific credentials through a secret manager, real market-data adapters, persistent storage, alerting, and independently verified execution behavior. This project does not claim or imply guaranteed profitability.
