from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass(frozen=True)
class NewsEvent:
    timestamp: datetime
    currency: str
    impact: str
    title: str=''

@dataclass(frozen=True)
class NewsPolicy:
    block_high_impact: bool=True
    before_minutes: int=15
    after_minutes: int=15

def is_blocked(ts: datetime, currencies: set[str], events: list[NewsEvent], policy: NewsPolicy=NewsPolicy()) -> bool:
    if not policy.block_high_impact: return False
    for e in events:
        if e.currency.upper() not in {c.upper() for c in currencies} or e.impact.lower()!='high': continue
        if e.timestamp-timedelta(minutes=policy.before_minutes) <= ts <= e.timestamp+timedelta(minutes=policy.after_minutes): return True
    return False
