from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

PAIR_CURRENCIES = {
    "EURUSD": {"EUR", "USD"}, "GBPUSD": {"GBP", "USD"}, "USDJPY": {"USD", "JPY"},
    "USDCHF": {"USD", "CHF"}, "AUDUSD": {"AUD", "USD"}, "USDCAD": {"USD", "CAD"},
    "NZDUSD": {"NZD", "USD"},
}


@dataclass(frozen=True)
class NewsEvent:
    timestamp: datetime
    currency: str
    impact: str
    title: str = ""


@dataclass(frozen=True)
class NewsPolicy:
    block_high_impact: bool = True
    before_minutes: int = 15
    after_minutes: int = 15
    block_medium_impact: bool = False

    def __post_init__(self) -> None:
        if self.before_minutes < 0 or self.after_minutes < 0:
            raise ValueError("news windows must be non-negative")


def currencies_for_pair(symbol: str) -> set[str]:
    normalized = symbol.replace("/", "").upper()
    if normalized in PAIR_CURRENCIES:
        return set(PAIR_CURRENCIES[normalized])
    if len(normalized) == 6 and normalized.isalpha():
        return {normalized[:3], normalized[3:]}
    raise ValueError(f"unsupported FX symbol: {symbol}")


def is_blocked(
    ts: datetime,
    currencies: set[str],
    events: list[NewsEvent],
    policy: NewsPolicy = NewsPolicy(),
) -> bool:
    if not currencies:
        return False
    target = {c.upper() for c in currencies}
    for event in events:
        impact = event.impact.lower()
        blocked_impact = impact == "high" and policy.block_high_impact or impact == "medium" and policy.block_medium_impact
        if not blocked_impact or event.currency.upper() not in target:
            continue
        start = event.timestamp - timedelta(minutes=policy.before_minutes)
        end = event.timestamp + timedelta(minutes=policy.after_minutes)
        if start <= ts <= end:
            return True
    return False


def is_pair_blocked(
    ts: datetime,
    symbol: str,
    events: list[NewsEvent],
    policy: NewsPolicy = NewsPolicy(),
) -> bool:
    return is_blocked(ts, currencies_for_pair(symbol), events, policy)
