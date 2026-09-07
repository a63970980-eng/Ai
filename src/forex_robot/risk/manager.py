from __future__ import annotations

import math

from forex_robot.domain.models import PositionSizeRequest, PositionSizeResponse


class RiskManager:
    """Deterministic position sizing; never places or modifies broker orders."""

    def position_size(self, request: PositionSizeRequest) -> PositionSizeResponse:
        values = (
            request.equity,
            request.risk_fraction,
            request.entry,
            request.stop_loss,
            request.pip_value_per_unit,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("position sizing inputs must be finite")
        stop_distance = abs(request.entry - request.stop_loss)
        if stop_distance <= 0:
            raise ValueError("stop_loss must differ from entry")

        risk_amount = request.equity * request.risk_fraction
        if risk_amount <= 0:
            raise ValueError("risk amount must be positive")
        units = risk_amount / (stop_distance * request.pip_value_per_unit)
        if not math.isfinite(units) or units <= 0:
            raise ValueError("calculated position size is invalid")
        return PositionSizeResponse(
            units=round(units, 4),
            risk_amount=round(risk_amount, 2),
            stop_distance=stop_distance,
        )
