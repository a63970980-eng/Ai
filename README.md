# AI Forex Trading Robot

Research-grade architecture for Forex scalping: market validation, technical features, regime detection, multi-strategy ensemble, AI scoring boundary, deterministic risk gates, backtesting, Monte Carlo robustness, and paper execution.

## Safety model

- Live trading is **OFF by default**.
- Paper trading is the default execution path.
- AI/model scores cannot bypass risk controls.
- Daily loss, drawdown, position-count and spread gates can halt execution.
- Broker credentials must be supplied through environment/secrets; never commit them.
- Backtests must include transaction costs and must not use future candles.

## Architecture

`Market Data → Validation → Features → Regime → Strategies → Ensemble/AI → Risk Gate → Execution Gateway → Broker`

Research path: `Historical Data → Backtest → Walk-forward/robustness analysis → Paper Trading → controlled production`

## Run

```bash
python -m pip install -e '.[dev]'
uvicorn forex_robot.api:app --reload
pytest
ruff check .
```

No performance claim or profitability guarantee is made. Real trading should only be enabled after independent validation, broker testing, operational monitoring and an explicit risk review.
