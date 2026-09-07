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
    """In-memory paper broker with idempotent client order IDs."""

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

    def place(self, order: OrderRequest) -> str:
        if order.units <= 0:
            raise ValueError("units must be positive")
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
                order.symbol, order.side, order.units, order.entry, order.stop_loss, order.take_profit
            )
        return order_id

    def modify(self, order_id: str, stop_loss: float | None = None, take_profit: float | None = None) -> None:
        if order_id not in self._positions:
            raise KeyError(order_id)
        position = self._positions[order_id]
        self._positions[order_id] = BrokerPosition(
            position.symbol,
            position.side,
            position.units,
            position.entry,
            stop_loss if stop_loss is not None else position.stop_loss,
            take_profit if take_profit is not None else position.take_profit,
        )

    def close(self, position_id: str) -> None:
        self._positions.pop(position_id, None)

    def cancel(self, order_id: str) -> None:
        self._orders.pop(order_id, None)
