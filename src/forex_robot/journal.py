from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime

@dataclass(frozen=True)
class TradeJournalEntry:
    timestamp:datetime; pair:str; direction:str; entry:float; stop_loss:float; take_profit:float; units:float
    risk:float; signal_score:float; strategy:str; regime:str; session:str; spread:float; slippage:float
    ai_analysis:str=''; result:float=0.; r_multiple:float=0.; exit_reason:str=''
    def to_dict(self): return asdict(self)

class Journal:
    def __init__(self): self.entries:list[TradeJournalEntry]=[]
    def record(self,entry:TradeJournalEntry)->None: self.entries.append(entry)
    def all(self): return [e.to_dict() for e in self.entries]
