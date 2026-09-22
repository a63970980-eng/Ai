from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from forex_robot.domain.trading import MarketTick


@dataclass(frozen=True)
class CandleFeed:
    provider: str
    symbol: str
    granularity: str
    candles: pd.DataFrame


class OKXMarketData:
    """Read-only OKX market-data adapter; trading credentials are never used here."""

    INTERVALS = {"1m":"1m","3m":"3m","5m":"5m","15m":"15m","30m":"30m","1h":"1H","2h":"2H","4h":"4H","6h":"6H","12h":"12H","1d":"1D"}

    def __init__(self, base_url: str = "https://openapi.okx.com"):
        self.base_url = base_url.rstrip("/")
        self.provider_name = "okx-demo"

    @staticmethod
    def _symbol(symbol: str) -> str:
        s = symbol.upper().replace("/", "-").replace("_", "-")
        if s == "BTCUSDT": return "BTC-USDT"
        if s == "ETHUSDT": return "ETH-USDT"
        return s

    def _get(self, path: str, params: dict) -> object:
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}{path}?{query}" if query else f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"ai-crypto-quant/2.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        if data.get("code") != "0":
            raise ValueError(str(data.get("msg", "OKX API error")))
        return data.get("data", [])

    def candles(self, symbol: str, granularity: str = "15m", count: int = 500) -> CandleFeed:
        if count < 30 or count > 1000: raise ValueError("count must be between 30 and 1000")
        bar = self.INTERVALS.get(granularity.lower())
        if bar is None: raise ValueError(f"unsupported OKX interval: {granularity}")
        raw = self._get("/api/v5/market/candles", {"instId":self._symbol(symbol),"bar":bar,"limit":min(count,300)})
        rows = []
        for k in reversed(raw):
            rows.append({"timestamp":datetime.fromtimestamp(int(k[0])/1000,tz=timezone.utc),"open":float(k[1]),"high":float(k[2]),"low":float(k[3]),"close":float(k[4]),"volume":float(k[5]),"confirm":int(k[8]) if len(k)>8 else 1})
        frame = pd.DataFrame(rows)
        if not frame.empty: frame = frame[frame["confirm"] == 1].drop(columns=["confirm"])
        return CandleFeed("okx", self._symbol(symbol), bar, frame)

    def price(self, symbol: str) -> MarketTick:
        raw = self._get("/api/v5/market/ticker", {"instId":self._symbol(symbol)})
        if not raw: raise ValueError("OKX returned no ticker")
        tick = raw[0]; bid, ask = float(tick["bidPx"]), float(tick["askPx"])
        if bid <= 0 or ask < bid: raise ValueError("invalid OKX bid/ask")
        return MarketTick(self._symbol(symbol), datetime.now(timezone.utc), bid, ask)


def build_market_feed() -> OKXMarketData:
    return OKXMarketData()
