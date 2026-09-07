import pandas as pd
import pytest

from forex_robot.backtest.exits import BacktestExitConfig


def test_dynamic_exit_config_supports_partial_targets():
    cfg = BacktestExitConfig(
        take_profit_multiples=(1.0, 2.0, 3.0),
        partial_exit_fractions=(0.25, 0.25, 0.25),
        break_even_after_r=1.0,
        trailing_atr_multiple=1.5,
    )
    assert cfg.take_profit_multiples == (1.0, 2.0, 3.0)
    assert sum(cfg.partial_exit_fractions) == 0.75


def test_dynamic_exit_config_rejects_fraction_overflow():
    with pytest.raises(ValueError, match="cannot exceed"):
        BacktestExitConfig(partial_exit_fractions=(0.6, 0.5, 0.1, 0.1))


def test_dynamic_exit_config_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="equal length"):
        BacktestExitConfig(
            take_profit_multiples=(1.0, 2.0),
            partial_exit_fractions=(1.0,),
        )
