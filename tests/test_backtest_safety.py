import pandas as pd
import pytest

from forex_robot.backtest.engine import run_backtest
from forex_robot.domain.models import Side, Signal


def frame(n=8):
    close = pd.Series([1.1000 + i * 0.001 for i in range(n)])
    return pd.DataFrame({"open": close, "high": close + 0.0005, "low": close - 0.0005, "close": close})


def signal(_history):
    return Signal(
        symbol="EURUSD", side=Side.BUY, confidence=0.9, entry=1.1,
        stop_loss=1.099, take_profit=1.2, reason="test", timestamp=pd.Timestamp.now(tz="UTC").to_pydatetime(),
    )


def test_backtest_uses_risk_based_position_size():
    result = run_backtest(frame(), signal, risk_per_trade=0.01, account_equity=100_000)
    assert result.trades == 1
    assert result.trade_log[0].risk_amount == 1000
    assert result.trade_log[0].units > 0


def test_backtest_rejects_nonfinite_costs():
    with pytest.raises(ValueError):
        run_backtest(frame(), signal, spread=float("nan"))


def test_backtest_rejects_invalid_ohlc():
    bad = frame(); bad.loc[0, "low"] = -1
    with pytest.raises(ValueError):
        run_backtest(bad, signal)
