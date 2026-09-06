from __future__ import annotations

from abc import ABC, abstractmethod
from forex_robot.domain.models import OrderRequest


class Broker(ABC):
    @abstractmethod
    def submit(self, order: OrderRequest) -> str: ...


class PaperBroker(Broker):
    def __init__(self) -> None:
        self.orders: list[OrderRequest] = []

    def submit(self, order: OrderRequest) -> str:
        self.orders.append(order)
        return f"PAPER-{len(self.orders):08d}"


class ExecutionGateway:
    def __init__(self, broker: Broker, live_enabled: bool = False):
        self.broker = broker
        self.live_enabled = live_enabled

    def submit(self, order: OrderRequest) -> str:
        if not self.live_enabled and not isinstance(self.broker, PaperBroker):
            raise RuntimeError("live execution is disabled")
        return self.broker.submit(order)
