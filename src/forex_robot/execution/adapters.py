from __future__ import annotations
from forex_robot.execution.broker import BrokerAdapter

class ExternalBrokerNotConfigured(RuntimeError): pass

class MT5Adapter(BrokerAdapter):
    def __init__(self, **credentials): self.credentials=credentials
    def _unavailable(self): raise ExternalBrokerNotConfigured('MT5 credentials/client are not configured')
    account=_unavailable; positions=_unavailable; price=_unavailable; place=_unavailable; modify=_unavailable; close=_unavailable; cancel=_unavailable

class OandaAdapter(MT5Adapter):
    pass

class CTraderAdapter(MT5Adapter):
    pass
