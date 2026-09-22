from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any

from forex_robot.domain.trading import OrderRequest


class OKXClient:
    """Minimal OKX V5 client with Demo Trading safety boundary."""

    def __init__(self, base_url: str | None = None, demo: bool | None = None) -> None:
        self.base_url = (base_url or os.getenv("OKX_REST_URL", "https://openapi.okx.com")).rstrip("/")
        self.api_key = os.getenv("OKX_API_KEY", "")
        self.secret_key = os.getenv("OKX_SECRET_KEY", "")
        self.passphrase = os.getenv("OKX_PASSPHRASE", "")
        self.demo = (os.getenv("OKX_DEMO", "true").lower() in {"1","true","yes","on"}) if demo is None else demo

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.secret_key and self.passphrase)

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        s = symbol.upper().replace("/", "-").replace("_", "-")
        if s == "BTCUSDT": return "BTC-USDT"
        if s == "ETHUSDT": return "ETH-USDT"
        return s

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None, private: bool = True) -> list[dict[str, Any]]:
        payload = json.dumps(body or {}, separators=(",", ":")) if method != "GET" else ""
        timestamp = self._timestamp()
        headers = {"Content-Type":"application/json","Accept":"application/json","User-Agent":"ai-crypto-quant/2.0"}
        if private:
            if not self.configured: raise RuntimeError("OKX API credentials are not configured")
            prehash = timestamp + method.upper() + path + payload
            signature = base64.b64encode(hmac.new(self.secret_key.encode(), prehash.encode(), hashlib.sha256).digest()).decode()
            headers.update({"OK-ACCESS-KEY":self.api_key,"OK-ACCESS-SIGN":signature,"OK-ACCESS-TIMESTAMP":timestamp,"OK-ACCESS-PASSPHRASE":self.passphrase})
        if self.demo: headers["x-simulated-trading"] = "1"
        req = urllib.request.Request(self.base_url + path, data=payload.encode() if payload else None, headers=headers, method=method.upper())
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode())
        if result.get("code") != "0": raise RuntimeError(f"OKX {result.get('code')}: {result.get('msg')}")
        for item in result.get("data", []):
            if str(item.get("sCode", "0")) != "0": raise RuntimeError(f"OKX order error {item.get('sCode')}: {item.get('sMsg')}")
        return result.get("data", [])

    def account_balance(self, ccy: str | None = None) -> list[dict[str, Any]]:
        path = "/api/v5/account/balance" + (("?ccy=" + ccy.upper()) if ccy else "")
        return self._request("GET", path, private=True)

    def place_market_order(self, order: OrderRequest, quote_ccy: str = "USDT") -> list[dict[str, Any]]:
        side = order.side.lower()
        if side not in {"buy", "sell"}: raise ValueError("OKX side must be buy or sell")
        inst_id = self.normalize_symbol(order.symbol)
        body = {"instId":inst_id,"tdMode":"cash","side":side,"ordType":"market","sz":str(order.units),"clOrdId":order.client_order_id[:32]}
        if side == "buy": body["tgtCcy"] = quote_ccy.upper()
        return self._request("POST", "/api/v5/trade/order", body, private=True)

    def cancel_order(self, symbol: str, order_id: str) -> list[dict[str, Any]]:
        return self._request("POST", "/api/v5/trade/cancel-order", {"instId":self.normalize_symbol(symbol),"ordId":order_id}, private=True)
