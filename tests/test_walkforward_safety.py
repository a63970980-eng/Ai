import pandas as pd

from forex_robot.backtest.walkforward import windows, evaluate_walk_forward
from forex_robot.domain.models import Signal, Side


def frame(n=30):
    close = pd.Series([1.1 + i * 0.001 for i in range(n)])
    return pd.DataFrame({"open": close, "high": close + .0002, "low": close - .0002, "close": close})


def no_signal(_history):
    return None


def test_windows_are_non_overlapping_by_default():
    ws = windows(30, 10, 5, 5)
    assert len(ws) == 2
    assert ws[0].test_end == ws[1].train_start


def test_evaluation_returns_validation_and_oos_test_results():
    result = evaluate_walk_forward(frame(), no_signal, train=10, validation=5, test=5)
    assert len(result) == 2
    assert result[0].validation.trades == 0
    assert result[0].test.trades == 0
