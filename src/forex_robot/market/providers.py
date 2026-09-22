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

class BinanceMarketData:
    """Read-only Binance Spot market-data adapter. Execution is deliberately separate."""
    INTERVALS = {"1m":"1m","3m":"3m","5m":"5m","15m":"15m","30m":"30m","1h":"1h","2h":"2h","4h":"4h","6h":"6h","12h":"12h","1d":"1d"}

    def __init__(self, base_url: str = "https://api.binance.com"):
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _symbol(symbol: str) -> str:
        return symbol.replace("/", "").replace("_","").upper()

    def _get(self, path: str, params: dict) -> object:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"ai-crypto-quant/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data, dict) and "code" in data and int(data.get("code",0)) < 0:
            raise ValueError(str(data.get("msg","Binance API error")))
        return data

    def candles(self, symbol: str, granularity: str = "1m", count: int = 500) -> CandleFeed:
        if count < 30 or count > 1000: raise ValueError("count must be between 30 and 1000")
        interval = self.INTERVALS.get(granularity.lower())
        if interval is None: raise ValueError(f"unsupported Binance interval: {granularity}")
        raw = self._get("/api/v3/klines", {"symbol":self._symbol(symbol),"interval":interval,"limit":count})
        rows = []
        for k in raw:
            rows.append({"timestamp":datetime.fromtimestamp(int(k[0])/1000,tz=timezone.utc),"open":float(k[1]),"high":float(k[2]),"low":float(k[3]),"close":float(k[4]),"volume":float(k[5])})
        return CandleFeed("binance", symbol.upper(), interval, pd.DataFrame(rows))

    def price(self, symbol: str) -> MarketTick:
        raw = self._get("/api/v3/ticker/bookTicker", {"symbol":self._symbol(symbol)})
        bid, ask = float(raw["bidPrice"]), float(raw["askPrice"])
        if bid <= 0 or ask < bid: raise ValueError("invalid Binance bid/ask")
        return MarketTick(self._symbol(symbol), datetime.now(timezone.utc), bid, ask)

def build_market_feed() -> BinanceMarketData:
    return BinanceMarketData()
