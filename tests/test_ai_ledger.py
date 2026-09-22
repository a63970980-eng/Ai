from datetime import datetime, timezone

from forex_robot.ai.council import ModelOpinion
from forex_robot.ai.ledger import AILedger
from forex_robot.domain.models import Side, Signal


def _signal():
    return Signal(
        symbol="EUR_USD",
        side=Side.BUY,
        confidence=0.8,
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        reason="test",
        timestamp=datetime.now(timezone.utc),
    )


def test_ledger_records_and_settles(tmp_path):
    db = AILedger(str(tmp_path / "ledger.sqlite3"))
    db.record("eval-1", _signal(), [
        ModelOpinion("openrouter", "qwen/qwen3-32b", .8, .9, "LONG", "ok", 12.0),
        ModelOpinion("openrouter", "deepseek/deepseek-r1", .7, .8, "WAIT", "ok", 15.0),
    ])
    assert len(db.get("eval-1")) == 2
    assert db.settle("eval-1", 1.0) == 2
    rows = db.performance()
    assert {row["model"] for row in rows} == {"qwen/qwen3-32b", "deepseek/deepseek-r1"}
