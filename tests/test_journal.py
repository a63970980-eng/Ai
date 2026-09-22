from datetime import datetime, timezone

from forex_robot.journal import Journal, TradeJournalEntry


def test_journal_round_trip():
    journal = Journal(":memory:")
    journal.record(
        TradeJournalEntry(
            timestamp=datetime.now(timezone.utc),
            pair="EUR_USD",
            direction="buy",
            entry=1.1,
            stop_loss=1.099,
            take_profit=1.102,
            units=1000,
            risk=0.005,
            signal_score=0.8,
            strategy="paper",
            regime="trend",
            session="london",
            spread=0.0001,
            slippage=0.0,
            ai_analysis="test",
        )
    )
    rows = journal.all()
    assert len(rows) == 1
    assert rows[0]["pair"] == "EUR_USD"
    assert rows[0]["units"] == 1000
