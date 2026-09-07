from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Exposure:
    base: dict[str, float]
    quote: dict[str, float]
    gross: float
    net: float


def currency_exposure(positions: list[dict]) -> Exposure:
    base: dict[str, float] = {}
    quote: dict[str, float] = {}
    for position in positions:
        pair = str(position.get("symbol", "")).upper().replace("/", "")
        if len(pair) != 6 or not pair.isalpha():
            continue
        units = float(position.get("units", 0))
        if not isfinite(units):
            raise ValueError("position units must be finite")
        if units == 0:
            continue
        signed = abs(units) if str(position.get("side", "buy")).lower() == "buy" else -abs(units)
        b, q = pair[:3], pair[3:]
        base[b] = base.get(b, 0.0) + signed
        quote[q] = quote.get(q, 0.0) - signed
    gross = sum(abs(v) for v in base.values()) + sum(abs(v) for v in quote.values())
    net = sum(base.values()) + sum(quote.values())
    return Exposure(base, quote, gross, net)


def correlation_breach(correlation: float, threshold: float = 0.85) -> bool:
    if not isfinite(correlation) or not 0 < threshold <= 1:
        raise ValueError("correlation must be finite and threshold must be in (0, 1]")
    return abs(correlation) >= threshold


def portfolio_risk_breach(current_risk: float, proposed_risk: float, limit: float) -> bool:
    if min(current_risk, proposed_risk) < 0 or limit <= 0:
        raise ValueError("risk values must be non-negative and limit must be positive")
    return current_risk + proposed_risk > limit
