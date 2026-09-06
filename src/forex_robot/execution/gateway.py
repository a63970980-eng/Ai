from __future__ import annotations
from forex_robot.domain.trading import OrderRequest
from forex_robot.execution.broker import BrokerAdapter, PaperBroker

class ExecutionGateway:
    def __init__(self, broker:BrokerAdapter, live_enabled:bool=False):
        self.broker=broker; self.live_enabled=live_enabled
    def submit(self, order:OrderRequest)->str:
        if order.units<=0: raise ValueError('order units must be positive')
        if not self.live_enabled and not isinstance(self.broker,PaperBroker): raise RuntimeError('live execution is disabled')
        return self.broker.place(order)
    def modify(self,*args,**kwargs): return self.broker.modify(*args,**kwargs)
    def close(self,*args,**kwargs): return self.broker.close(*args,**kwargs)
    def cancel(self,*args,**kwargs): return self.broker.cancel(*args,**kwargs)
