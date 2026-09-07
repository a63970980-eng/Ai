from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from forex_robot.domain.trading import MarketTick, OrderRequest


@dataclass(frozen=True)
class BrokerPosition:
    symbol: str
    side: str
    units: float
    entry: float
    stop_loss: float | None = None
    take_profit: float | None = None


class BrokerAdapter(ABC):
    @abstractmethod
    def account(self) -> dict[str, float]: ...

    @abstractmethod
    def positions(self) -> list[BrokerPosition]: ...

    @abstractmethod
    def price(self, symbol: str) -> MarketTick: ...

    @abstractmethod
    def place(self, order: OrderRequest) -> str: ...

    @abstractmethod
    def modify(self, order_id: str, stop_loss: float | None = None, take_profit: float | None = None) -> None: ...

    @abstractmethod
    def close(self, position_id: str) -> None: ...

    @abstractmethod
    def cancel(self, order_id: str) -> None: ...


class PaperBroker(BrokerAdapter):
    """In-memory paper broker with idempotency and order-geometry validation."""

    def __init__(self, equity: float = 100_000.0) -> None:
        if equity <= 0:
            raise ValueError("equity must be positive")
        self._orders: dict[str, OrderRequest] = {}
        self._positions: dict[str, BrokerPosition] = {}
        self._seq = 0
        self._equity = float(equity)

    def account(self) -> dict[str, float]:
        return {"balance": self._equity, "equity": self._equity}

    def positions(self) -> list[BrokerPosition]:
        return list(self._positions.values())

    def price(self, symbol: str) -> MarketTick:
        raise RuntimeError(f"paper price feed not configured for {symbol}")

    @staticmethod
    def _validate_order(order: OrderRequest) -> None:
        if order.units <= 0 or order.entry <= 0:
            raise ValueError("units and entry must be positive")
        side = order.side.value if hasattr(order.side, "value") else str(order.side).lower()
        if side == "buy" and not (order.stop_loss < order.entry < order.take_profit):
            raise ValueError("BUY order requires stop_loss < entry < take_profit")
        if side == "sell" and not (order.take_profit < order.entry < order.stop_loss):
            raise ValueError("SELL order requires take_profit < entry < stop_loss")
        if side not in {"buy", "sell"}:
            raise ValueError("order side must be buy or sell")

    def place(self, order: OrderRequest) -> str:
        self._validate_order(order)
        if not order.client_order_id:
            self._seq += 1
            order_id = f"PAPER-{self._seq:08d}"
        else:
            order_id = order.client_order_id
        if order_id in self._orders:
            existing = self._orders[order_id]
            if existing != order:
                raise ValueError("client_order_id already used for a different order")
            return order_id
        self._orders[order_id] = order
        if not order.reduce_only:
            self._positions[order_id] = BrokerPosition(
                order.symbol, str(order.side.value), order.units, order.entry, order.stop_loss, order.take_profit
            )
        return order_id

    def modify(self, order_id: str, stop_loss: float | None = None, take_profit: float | None = None) -> None:
        if order_id not in self._positions:
            raise KeyError(order_id)
        position = self._positions[order_id]
        new_sl = stop_loss if stop_loss is not None else position.stop_loss
        new_tp = take_profit if take_profit is not None else position.take_profit
        if new_sl is not None and new_tp is not None:
            if position.side == "buy" and not new_sl < position.entry < new_tp:
                raise ValueError("BUY position requires stop_loss < entry < take_profit")
            if position.side == "sell" and not new_tp < position.entry < new_sl:
                raise ValueError("SELL position requires take_profit < entry < stop_loss")
        self._positions[order_id] = BrokerPosition(
            position.symbol, position.side, position.units, position.entry, new_sl, new_tp
        )

    def close(self, position_id: str) -> None:
        self._positions.pop(position_id, None)

    def cancel(self, order_id: str) -> None:
        self._orders.pop(order_id, None)
