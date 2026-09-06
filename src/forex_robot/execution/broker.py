from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from forex_robot.domain.trading import MarketTick, OrderRequest

@dataclass(frozen=True)
class BrokerPosition:
    symbol:str; side:str; units:float; entry:float; stop_loss:float|None=None; take_profit:float|None=None

class BrokerAdapter(ABC):
    @abstractmethod
    def account(self)->dict[str,float]: ...
    @abstractmethod
    def positions(self)->list[BrokerPosition]: ...
    @abstractmethod
    def price(self,symbol:str)->MarketTick: ...
    @abstractmethod
    def place(self,order:OrderRequest)->str: ...
    @abstractmethod
    def modify(self,order_id:str,stop_loss:float|None=None,take_profit:float|None=None)->None: ...
    @abstractmethod
    def close(self,position_id:str)->None: ...
    @abstractmethod
    def cancel(self,order_id:str)->None: ...

class PaperBroker(BrokerAdapter):
    def __init__(self): self._orders={}; self._positions={}; self._seq=0; self._equity=100000.0
    def account(self): return {'balance':self._equity,'equity':self._equity}
    def positions(self): return list(self._positions.values())
    def price(self,symbol): raise RuntimeError('paper price feed not configured')
    def place(self,order):
        if order.units<=0: raise ValueError('units must be positive')
        self._seq+=1; oid=order.client_order_id or f'PAPER-{self._seq:08d}'; self._orders[oid]=order
        self._positions[oid]=BrokerPosition(order.symbol,order.side,order.units,order.entry,order.stop_loss,order.take_profit); return oid
    def modify(self,order_id,stop_loss=None,take_profit=None):
        p=self._positions[order_id]; self._positions[order_id]=BrokerPosition(p.symbol,p.side,p.units,p.entry,stop_loss if stop_loss is not None else p.stop_loss,take_profit if take_profit is not None else p.take_profit)
    def close(self,position_id): self._positions.pop(position_id,None)
    def cancel(self,order_id): self._orders.pop(order_id,None)
