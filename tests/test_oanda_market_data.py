from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from forex_robot.market.providers import OandaMarketData


class _Response:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._body


def test_oanda_candles_ignore_incomplete_and_sort(monkeypatch):
    payload = {
        "candles": [
            {
                "time": "2026-09-13T10:02:00Z",
                "complete": True,
                "mid": {"o": "1.1010", "h": "1.1020", "l": "1.1000", "c": "1.1015"},
                "volume": 20,
            },
            {
                "time": "2026-09-13T10:03:00Z",
                "complete": False,
                "mid": {"o": "1.1015", "h": "1.1030", "l": "1.1010", "c": "1.1025"},
                "volume": 25,
            },
            {
                "time": "2026-09-13T10:01:00Z",
                "complete": True,
                "mid": {"o": "1.1000", "h": "1.1010", "l": "1.0990", "c": "1.1010"},
                "volume": 18,
            },
        ]
    }
    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: _Response(payload))

    feed = OandaMarketData("test-key").candles("eur/usd", "M1", 30)

    assert list(feed.candles["close"]) == [1.1010, 1.1015]
    assert feed.candles["timestamp"].iloc[0] == datetime(2026, 9, 13, 10, 1, tzinfo=timezone.utc)


def test_oanda_price_requires_account_id():
    with pytest.raises(ValueError, match="OANDA_ACCOUNT_ID"):
        OandaMarketData("test-key").price("EUR_USD")


def test_oanda_price_validates_bid_ask(monkeypatch):
    payload = {
        "prices": [
            {
                "instrument": "EUR_USD",
                "time": "2026-09-13T10:05:00Z",
                "bids": [{"price": "1.10000"}],
                "asks": [{"price": "1.10020"}],
            }
        ]
    }
    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: _Response(payload))

    tick = OandaMarketData("test-key", "101-001-1234567-001").price("EUR_USD")

    assert tick.bid == 1.1
    assert tick.ask == 1.1002
    assert tick.spread == pytest.approx(0.0002)
