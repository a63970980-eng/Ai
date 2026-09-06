from __future__ import annotations

from forex_robot.domain.models import PositionSizeRequest, PositionSizeResponse


class RiskManager:
    """Deterministic risk controls; no broker order is placed here."""

    def position_size(self, request: PositionSizeRequest) -> PositionSizeResponse:
        stop_distance = abs(request.entry - request.stop_loss)
        if stop_distance <= 0:
            raise ValueError("stop_loss must differ from entry")

        risk_amount = request.equity * request.risk_fraction
        units = risk_amount / (stop_distance * request.pip_value_per_unit)
        return PositionSizeResponse(
            units=round(units, 4),
            risk_amount=round(risk_amount, 2),
            stop_distance=stop_distance,
        )
