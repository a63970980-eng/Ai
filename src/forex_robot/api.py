from __future__ import annotations

from fastapi import FastAPI, HTTPException

from forex_robot.domain.models import PositionSizeRequest, PositionSizeResponse
from forex_robot.risk.manager import RiskManager

app = FastAPI(title="AI Forex Trading Robot", version="0.1.0")
risk_manager = RiskManager()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-forex-trading-robot"}


@app.post("/risk/position-size", response_model=PositionSizeResponse)
def position_size(request: PositionSizeRequest) -> PositionSizeResponse:
    try:
        return risk_manager.position_size(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
