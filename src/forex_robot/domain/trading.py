from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class MarketTick:
    symbol:str; timestamp:datetime; bid:float; ask:float
    @property
    def spread(self)->float: return self.ask-self.bid
    @property
    def mid(self)->float: return (self.bid+self.ask)/2

@dataclass(frozen=True)
class RiskLimits:
    max_risk_fraction:float=.005; max_daily_loss_fraction:float=.02; max_drawdown_fraction:float=.10
    max_open_positions:int=3; max_spread:float=.00020; max_slippage:float=.00010
    max_consecutive_losses:int=3; max_portfolio_risk:float=.02

@dataclass(frozen=True)
class OrderRequest:
    symbol:str; side:str; units:float; entry:float; stop_loss:float; take_profit:float
    client_order_id:str=''; reduce_only:bool=False

@dataclass
class AccountState:
    equity:float; day_start_equity:float; peak_equity:float; open_positions:int=0
    consecutive_losses:int=0; portfolio_risk:float=0.0; kill_switch:bool=False
    currency_exposure:dict[str,float]=field(default_factory=dict)
