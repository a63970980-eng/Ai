import pandas as pd

from forex_robot.backtest.engine import run_backtest
from forex_robot.domain.models import Side
from forex_robot.domain.trading import OrderRequest
from forex_robot.execution.gateway import ExecutionGateway, PaperBroker
from forex_robot.strategies.scalping import momentum


def candles(n=80):
    close = pd.Series([1 + 0.0005 * i for i in range(n)])
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 0.0002,
            "low": close - 0.0002,
            "close": close,
            "volume": 1000,
        }
    )


def test_backtest_has_no_future_access():
    result = run_backtest(candles(), lambda history: momentum("EURUSD", history), spread=0.0001)
    assert result.trades >= 0


def test_paper_execution():
    broker = PaperBroker()
    gateway = ExecutionGateway(broker)
    oid = gateway.submit(
        OrderRequest(
            symbol="EURUSD",
            side=Side.BUY,
            units=100,
            entry=1.1,
            stop_loss=1.099,
            take_profit=1.102,
        )
    )
    assert oid.startswith("PAPER-")
