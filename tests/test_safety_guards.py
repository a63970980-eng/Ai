import pandas as pd
import pytest
from dataclasses import replace

from forex_robot.domain.models import Side, Signal
from forex_robot.execution.broker import PaperBroker
from forex_robot.domain.trading import OrderRequest
from forex_robot.ensemble import Ensemble
from forex_robot.market.news import NewsEvent, NewsPolicy, is_pair_blocked


def signal(side: Side, confidence: float = 0.8) -> Signal:
    return Signal(
        symbol="EURUSD", side=side, confidence=confidence, entry=1.1,
        stop_loss=1.099 if side is Side.BUY else 1.101,
        take_profit=1.102 if side is Side.BUY else 1.098,
        reason="test", timestamp=pd.Timestamp("2026-01-01", tz="UTC").to_pydatetime(),
    )


def test_weighted_ensemble_reports_agreement():
    frame = pd.DataFrame({"open": [1.1] * 20, "high": [1.101] * 20, "low": [1.099] * 20, "close": [1.1] * 20})
    result = Ensemble([lambda _s, _d: signal(Side.BUY), lambda _s, _d: signal(Side.BUY)], [2.0, 1.0]).generate("EURUSD", frame)
    assert result.signal is not None
    assert result.agreement == 1.0


def test_paper_broker_is_idempotent():
    broker = PaperBroker()
    order = OrderRequest("EURUSD", "buy", 100, 1.1, 1.099, 1.102, "client-1")
    assert broker.place(order) == "client-1"
    assert broker.place(order) == "client-1"
    assert len(broker.positions()) == 1
    with pytest.raises(ValueError):
        broker.place(replace(order, units=200))


def test_pair_news_gate_matches_currency():
    event = NewsEvent(pd.Timestamp("2026-01-01T12:00:00Z").to_pydatetime(), "USD", "high")
    policy = NewsPolicy(before_minutes=15, after_minutes=15)
    assert is_pair_blocked(pd.Timestamp("2026-01-01T12:10:00Z").to_pydatetime(), "EURUSD", [event], policy)
    assert not is_pair_blocked(pd.Timestamp("2026-01-01T12:10:00Z").to_pydatetime(), "GBPUSD", [NewsEvent(event.timestamp, "JPY", "high")], policy)
