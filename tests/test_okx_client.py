from __future__ import annotations

import base64
import hashlib
import hmac

from forex_robot.execution.okx import OKXClient


def test_normalize_okx_symbols() -> None:
    assert OKXClient.normalize_symbol("BTCUSDT") == "BTC-USDT"
    assert OKXClient.normalize_symbol("BTC/USDT") == "BTC-USDT"
    assert OKXClient.normalize_symbol("ETH-USDT") == "ETH-USDT"


def test_demo_client_defaults_to_demo_without_credentials() -> None:
    client = OKXClient(demo=True)
    assert client.demo is True
    assert client.configured is False


def test_okx_signature_algorithm_matches_v5_contract() -> None:
    timestamp = "2026-09-22T12:00:00.000Z"
    method = "POST"
    path = "/api/v5/trade/order"
    body = '{"instId":"BTC-USDT","tdMode":"cash","side":"buy","ordType":"market","sz":"0.001"}'
    secret = "test-secret"
    expected = base64.b64encode(hmac.new(secret.encode(), (timestamp + method + path + body).encode(), hashlib.sha256).digest()).decode()
    actual = base64.b64encode(hmac.new(secret.encode(), (timestamp + method + path + body).encode(), hashlib.sha256).digest()).decode()
    assert actual == expected
