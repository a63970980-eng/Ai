from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class Signal(BaseModel):
    symbol: str
    side: Side
    confidence: float = Field(ge=0, le=1)
    entry: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    reason: str
    timestamp: datetime


class PositionSizeRequest(BaseModel):
    equity: float = Field(gt=0)
    risk_fraction: float = Field(gt=0, le=0.05)
    entry: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    pip_value_per_unit: float = Field(gt=0)


class PositionSizeResponse(BaseModel):
    units: float
    risk_amount: float
    stop_distance: float


class Candle(BaseModel):
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0, default=0)
