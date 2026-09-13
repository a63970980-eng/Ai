from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from forex_robot.domain.trading import MarketTick


@dataclass(frozen=True)
class CandleFeed:
    provider: str
    symbol: str
    granularity: str
    candles: pd.DataFrame


class OandaMarketData:
    """Read-only OANDA market-data adapter. It never places or modifies orders."""

    def __init__(self, api_key: str, account_id: str = "", environment: str = "practice") -> None:
        self.api_key = api_key
        self.account_id = account_id
        host = "api-fxpractice.oanda.com" if environment.lower() != "live" else "api-fxtrade.oanda.com"
        self.base_url = f"https://{host}"

    def _request_json(self, url: str) -> dict:
        request = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))

    def candles(self, symbol: str, granularity: str = "M1", count: int = 250) -> CandleFeed:
        if count < 30 or count > 5000:
            raise ValueError("count must be between 30 and 5000")
        instrument = symbol.replace("/", "_").upper()
        query = urllib.parse.urlencode({"granularity": granularity.upper(), "count": count, "price": "M"})
        payload = self._request_json(f"{self.base_url}/v3/instruments/{instrument}/candles?{query}")
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

    def price(self, symbol: str) -> MarketTick:
        if not self.account_id:
            raise ValueError("OANDA_ACCOUNT_ID is required for bid/ask spread checks")
        instrument = symbol.replace("/", "_").upper()
        query = urllib.parse.urlencode({"instruments": instrument})
        payload = self._request_json(f"{self.base_url}/v3/accounts/{self.account_id}/pricing?{query}")
        prices = payload.get("prices", [])
        if not prices:
            raise ValueError(f"no OANDA price returned for {instrument}")
        item = prices[0]
        timestamp = datetime.fromisoformat(str(item["time"]).replace("Z", "+00:00"))
        bid = float(item["bids"][0]["price"])
        ask = float(item["asks"][0]["price"])
        if bid <= 0 or ask <= 0 or ask < bid:
            raise ValueError("invalid OANDA bid/ask price")
        return MarketTick(instrument, timestamp, bid, ask)


def build_market_feed() -> OandaMarketData | None:
    key = os.getenv("OANDA_API_KEY", "").strip()
    if not key:
        return None
    return OandaMarketData(
        key,
        os.getenv("OANDA_ACCOUNT_ID", "").strip(),
        os.getenv("OANDA_ENVIRONMENT", "practice"),
    )
