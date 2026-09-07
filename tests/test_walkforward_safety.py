import pandas as pd

from forex_robot.backtest.walkforward import windows, evaluate_walk_forward


def frame(n=30):
    close = pd.Series([1.1 + i * 0.001 for i in range(n)])
    return pd.DataFrame({"open": close, "high": close + .0002, "low": close - .0002, "close": close})


def no_signal(_history):
    return None


def test_windows_keep_test_periods_non_overlapping_by_default():
    ws = windows(30, 10, 5, 5)
    assert len(ws) == 3
    for previous, current in zip(ws, ws[1:]):
        current_test_start = current.validation_end
        assert previous.test_end <= current_test_start


def test_evaluation_returns_validation_and_oos_test_results():
    result = evaluate_walk_forward(frame(), no_signal, train=10, validation=5, test=5)
    assert len(result) == 3
    assert all(item.validation.trades == 0 for item in result)
    assert all(item.test.trades == 0 for item in result)
