import pytest

from forex_robot.domain.models import PositionSizeRequest
from forex_robot.risk.manager import RiskManager


def test_position_size_respects_risk_budget() -> None:
    result = RiskManager().position_size(
        PositionSizeRequest(
            equity=10_000,
            risk_fraction=0.01,
            entry=1.1000,
            stop_loss=1.0950,
            pip_value_per_unit=1,
        )
    )
    assert result.risk_amount == 100
    assert result.units == pytest.approx(20_000)


def test_equal_entry_and_stop_is_rejected() -> None:
    with pytest.raises(ValueError):
        RiskManager().position_size(
            PositionSizeRequest(
                equity=10_000,
                risk_fraction=0.01,
                entry=1.1,
                stop_loss=1.1,
                pip_value_per_unit=1,
            )
        )
