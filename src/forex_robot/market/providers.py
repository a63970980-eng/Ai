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


class _HttpMarketData:
    def _request_json(self, url: str, headers: dict[str, str] | None = None) -> dict:
        request = urllib.request.Request(url, headers=headers or {"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, dict) and payload.get("status") == "error":
            raise ValueError(str(payload.get("message", "market data provider error")))
        return payload


class OandaMarketData(_HttpMarketData):
    """Read-only OANDA market-data adapter. It never places or modifies orders."""

    def __init__(self, api_key: str, account_id: str = "", environment: str = "practice") -> None:
        self.api_key = api_key
        self.account_id = account_id
        host = "api-fxpractice.oanda.com" if environment.lower() != "live" else "api-fxtrade.oanda.com"
        self.base_url = f"https://{host}"

    def _request_json(self, url: str) -> dict:
        return super()._request_json(
            url,
            headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
        )

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


class TwelveDataMarketData(_HttpMarketData):
    """Read-only Twelve Data Forex feed for real-market-data paper trading."""

    INTERVALS = {"M1": "1min", "M5": "5min", "M15": "15min", "H1": "1h"}

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    @staticmethod
    def _symbol(symbol: str) -> str:
        value = symbol.replace("_", "/").upper()
        if "/" not in value and len(value) == 6:
            value = f"{value[:3]}/{value[3:]}"
        return value

    def candles(self, symbol: str, granularity: str = "M1", count: int = 250) -> CandleFeed:
        if count < 30 or count > 5000:
            raise ValueError("count must be between 30 and 5000")
        interval = self.INTERVALS.get(granularity.upper())
        if interval is None:
            raise ValueError(f"unsupported Twelve Data interval: {granularity}")
        query = urllib.parse.urlencode(
            {"symbol": self._symbol(symbol), "interval": interval, "outputsize": count, "format": "JSON", "apikey": self.api_key}
        )
        payload = self._request_json(f"{self.base_url}/time_series?{query}")
        values = payload.get("values", [])
        rows: list[dict[str, object]] = []
        for candle in values:
            rows.append(
                {
                    "timestamp": datetime.fromisoformat(str(candle["datetime"]).replace("Z", "+00:00")),
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                    "volume": float(candle.get("volume", 0) or 0),
                }
            )
        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame = frame.sort_values("timestamp").reset_index(drop=True)
        return CandleFeed("twelve_data", symbol.upper(), granularity.upper(), frame)

    def price(self, symbol: str) -> MarketTick:
        query = urllib.parse.urlencode({"symbol": self._symbol(symbol), "apikey": self.api_key})
        payload = self._request_json(f"{self.base_url}/quote?{query}")
        bid = float(payload.get("bid", 0) or 0)
        ask = float(payload.get("ask", 0) or 0)
        if bid <= 0 or ask <= 0 or ask < bid:
            raise ValueError("Twelve Data quote did not provide a valid bid/ask")
        timestamp = datetime.now().astimezone()
        return MarketTick(self._symbol(symbol), timestamp, bid, ask)


def build_market_feed() -> TwelveDataMarketData | OandaMarketData | None:
    # Prefer Twelve Data when configured: it is independent of broker account availability.
    twelve_key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if twelve_key:
        return TwelveDataMarketData(twelve_key)

    oanda_key = os.getenv("OANDA_API_KEY", "").strip()
    if oanda_key:
        return OandaMarketData(
            oanda_key,
            os.getenv("OANDA_ACCOUNT_ID", "").strip(),
            os.getenv("OANDA_ENVIRONMENT", "practice"),
        )
    return None
