import pytest

from forex_robot.domain.models import Side
from forex_robot.exits import break_even_stop, build_exit_plan, trailing_stop


def test_exit_plan_has_configurable_targets():
    plan = build_exit_plan(Side.BUY, 1.1000, 0.0010, tp_multiples=(1.0, 2.0, 3.0))
    assert len(plan.take_profits) == 3
    assert plan.stop_loss < 1.1000 < plan.take_profits[0]


def test_break_even_and_trailing_only_improve_stop():
    be = break_even_stop(Side.BUY, 1.1000, 1.0990, 1.1010)
    assert be == 1.1000
    assert trailing_stop(Side.BUY, 1.1030, 0.0010, existing=be) >= be


def test_invalid_exit_parameters_are_rejected():
    with pytest.raises(ValueError):
        build_exit_plan(Side.BUY, 1.1, 0, tp_multiples=(1.0,))
    with pytest.raises(ValueError):
        trailing_stop(Side.BUY, 1.1, 0.001, multiplier=0)
