import pytest

from forex_robot.robustness.stress import connection_failure, stress_returns, validate_market_frame


def test_stress_is_deterministic_and_exposes_drawdown():
    first = stress_returns([1.0, -0.5, 2.0, -1.0], spread_factor=2.0, slippage_factor=2.0, volatility_factor=1.2)
    second = stress_returns([1.0, -0.5, 2.0, -1.0], spread_factor=2.0, slippage_factor=2.0, volatility_factor=1.2)
    assert first == second
    assert first.max_drawdown >= 0
    assert first.losing_streak >= 0


def test_stress_rejects_invalid_factors_and_returns():
    with pytest.raises(ValueError):
        stress_returns([1.0], spread_factor=0)
    with pytest.raises(ValueError):
        stress_returns([float("nan")])


def test_market_corruption_and_connection_failure_are_explicit():
    result = validate_market_frame([
        {"timestamp": "1", "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15},
        {"timestamp": "1", "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15},
        {"timestamp": "2", "open": -1, "high": 1.2, "low": 1.0, "close": 1.15},
        {"timestamp": "3", "open": 1.1},
    ])
    assert not result["healthy"]
    assert result["duplicate_timestamps"] == 1
    assert result["invalid_ohlc"] == 1
    assert result["missing_ohlc"] == 1
    assert connection_failure()["action"] == "halt_new_orders"
