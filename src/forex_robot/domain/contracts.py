from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

class Side(StrEnum): BUY='buy'; SELL='sell'
class Mode(StrEnum): BACKTEST='backtest'; PAPER='paper'; LIVE='live'

@dataclass(frozen=True)
class Tick:
    symbol:str; timestamp:datetime; bid:float; ask:float
    @property
    def spread(self)->float: return self.ask-self.bid
    @property
    def mid(self)->float: return (self.bid+self.ask)/2

@dataclass(frozen=True)
class SignalScore:
    total:float; verdict:str; components:dict[str,float]

@dataclass(frozen=True)
class Order:
    symbol:str; side:Side; units:float; entry:float; stop_loss:float; take_profit:float; client_id:str

@dataclass(frozen=True)
class Position:
    symbol:str; side:Side; units:float; entry:float; stop_loss:float; take_profit:float

@dataclass(frozen=True)
class RiskLimits:
    risk_per_trade:float=.005; daily_loss:float=.02; max_drawdown:float=.10
    max_positions:int=3; max_spread_pips:float=2.; max_slippage_pips:float=1.
    max_consecutive_losses:int=3; max_portfolio_risk:float=.02

@dataclass
class Account:
    equity:float; day_start:float; peak:float; open_positions:int=0; consecutive_losses:int=0; kill_switch:bool=False

@dataclass(frozen=True)
class Trade:
    timestamp:datetime; symbol:str; side:Side; entry:float; stop_loss:float; take_profit:float
    units:float; risk_amount:float; score:float; strategy:str; regime:str; session:str
    spread:float; slippage:float; ai_analysis:str=''; result:float=0.; r_multiple:float=0.; exit_reason:str=''

UTC=timezone.utc
