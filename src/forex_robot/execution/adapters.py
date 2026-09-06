from __future__ import annotations

from typing import Any, NoReturn

from forex_robot.domain.trading import MarketTick, OrderRequest
from forex_robot.execution.broker import BrokerAdapter, BrokerPosition


class ExternalBrokerNotConfigured(RuntimeError):
    pass


class MT5Adapter(BrokerAdapter):
    def __init__(self, **credentials: Any) -> None:
        self.credentials = credentials

    def _unavailable(self) -> NoReturn:
        raise ExternalBrokerNotConfigured("MT5 credentials/client are not configured")

    def account(self) -> dict[str, float]:
        self._unavailable()

    def positions(self) -> list[BrokerPosition]:
        self._unavailable()

    def price(self, symbol: str) -> MarketTick:
        self._unavailable()

    def place(self, order: OrderRequest) -> str:
        self._unavailable()

    def modify(
        self,
        order_id: str,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> None:
        self._unavailable()

    def close(self, position_id: str) -> None:
        self._unavailable()

    def cancel(self, order_id: str) -> None:
        self._unavailable()


class OandaAdapter(MT5Adapter):
    pass


class CTraderAdapter(MT5Adapter):
    pass
