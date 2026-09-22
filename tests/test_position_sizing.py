import pytest

from forex_robot.risk.sizing import calculate_position_size


def test_position_size_respects_risk_budget():
    result = calculate_position_size(100_000, 1.1000, 1.0990, 0.005)
    assert result.units == pytest.approx(500_000)
    assert result.risk_amount == pytest.approx(500)


def test_position_size_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_position_size(100_000, 1.1, 1.1, 0.005)
    with pytest.raises(ValueError):
        calculate_position_size(100_000, 1.1, 1.0, 0.06)
