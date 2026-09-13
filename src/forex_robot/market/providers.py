from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd


@dataclass(frozen=True)
class CandleFeed:
    provider: str
    symbol: str
    granularity: str
    candles: pd.DataFrame


class OandaMarketData:
    """Read-only OANDA candle feed. It never places or modifies orders."""

    def __init__(self, api_key: str, account_id: str = "", environment: str = "practice") -> None:
        self.api_key = api_key
        self.account_id = account_id
        host = "api-fxpractice.oanda.com" if environment.lower() != "live" else "api-fxtrade.oanda.com"
        self.base_url = f"https://{host}"

    def candles(self, symbol: str, granularity: str = "M1", count: int = 250) -> CandleFeed:
        if count < 30 or count > 5000:
            raise ValueError("count must be between 30 and 5000")
        instrument = symbol.replace("/", "_").upper()
        query = urllib.parse.urlencode({"granularity": granularity.upper(), "count": count, "price": "M"})
        request = urllib.request.Request(
            f"{self.base_url}/v3/instruments/{instrument}/candles?{query}",
            headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows: list[dict[str, object]] = []
        for candle in payload.get("candles", []):
            if not candle.get("complete", True):
                continue
            mid = candle.get("mid", {})
            rows.append(
                {
                    "timestamp": datetime.fromisoformat(str(candle["time"]).replace("Z", "+00:00")),
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": float(candle.get("volume", 0)),
                }
            )
        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame = frame.sort_values("timestamp").reset_index(drop=True)
        return CandleFeed("oanda", symbol.upper(), granularity.upper(), frame)


def build_market_feed() -> OandaMarketData | None:
    key = os.getenv("OANDA_API_KEY", "").strip()
    if not key:
        return None
    return OandaMarketData(key, os.getenv("OANDA_ACCOUNT_ID", "").strip(), os.getenv("OANDA_ENVIRONMENT", "practice"))
