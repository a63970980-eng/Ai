from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestExitConfig:
    """Optional dynamic-exit rules used by the deterministic backtest engine."""

    take_profit_multiples: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0)
    partial_exit_fractions: tuple[float, ...] = (0.25, 0.25, 0.25, 0.25)
    break_even_after_r: float | None = 1.0
    trailing_atr_multiple: float | None = 1.5

    def __post_init__(self) -> None:
        if not self.take_profit_multiples:
            raise ValueError("at least one take-profit multiple is required")
        if len(self.take_profit_multiples) != len(self.partial_exit_fractions):
            raise ValueError("TP multiples and partial fractions must have equal length")
        if any(m <= 0 for m in self.take_profit_multiples):
            raise ValueError("TP multiples must be positive")
        if any(f <= 0 for f in self.partial_exit_fractions):
            raise ValueError("partial exit fractions must be positive")
        if sum(self.partial_exit_fractions) > 1.0 + 1e-9:
            raise ValueError("partial exit fractions cannot exceed 100%")
        if self.break_even_after_r is not None and self.break_even_after_r < 0:
            raise ValueError("break-even trigger cannot be negative")
        if self.trailing_atr_multiple is not None and self.trailing_atr_multiple <= 0:
            raise ValueError("trailing ATR multiple must be positive")
