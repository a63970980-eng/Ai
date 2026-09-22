from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _db_path() -> str:
    configured = os.getenv("AI_LEDGER_DB")
    if configured:
        # Vercel's deployment filesystem is read-only except for /tmp.
        if os.getenv("VERCEL") and not os.path.isabs(configured):
            return str(Path("/tmp") / Path(configured).name)
        return configured
    return "/tmp/ai_ledger.sqlite3" if os.getenv("VERCEL") else str(Path("data") / "ai_ledger.sqlite3")


class AILedger:
    """SQLite ledger for AI opinions and realized outcomes."""

    def __init__(self, path: str | None = None) -> None:
        self.path = path or _db_path()
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS council_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                score REAL NOT NULL,
                confidence REAL NOT NULL,
                stance TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                error TEXT,
                outcome REAL,
                settled_at TEXT
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_ai_eval_id ON council_evaluations(evaluation_id)")

    def record(self, evaluation_id: str, signal: Any, opinions: list[Any]) -> None:
        created = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.executemany(
                """INSERT INTO council_evaluations
                (evaluation_id, created_at, symbol, side, provider, model, score,
                 confidence, stance, latency_ms, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(evaluation_id, created, signal.symbol, str(signal.side), op.provider,
                  op.model, op.score, op.confidence, op.stance, op.latency_ms, op.error)
                 for op in opinions],
            )

    def settle(self, evaluation_id: str, outcome: float) -> int:
        if outcome not in (-1.0, 0.0, 1.0):
            raise ValueError("outcome must be -1, 0, or 1")
        with self._connect() as db:
            cur = db.execute(
                """UPDATE council_evaluations SET outcome=?, settled_at=?
                   WHERE evaluation_id=? AND outcome IS NULL""",
                (outcome, datetime.now(timezone.utc).isoformat(), evaluation_id),
            )
            return cur.rowcount

    def performance(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT provider, model, COUNT(*) AS evaluations,
                   SUM(CASE WHEN outcome IS NOT NULL THEN 1 ELSE 0 END) AS settled,
                   AVG(CASE WHEN outcome IS NOT NULL THEN
                     CASE WHEN (stance='LONG' AND outcome=1)
                       OR (stance='SHORT' AND outcome=-1)
                       OR (stance='WAIT' AND outcome=0) THEN 1.0 ELSE 0.0 END
                   END) AS accuracy,
                   AVG(confidence) AS avg_confidence,
                   AVG(latency_ms) AS avg_latency_ms
                   FROM council_evaluations GROUP BY provider, model
                   ORDER BY accuracy DESC NULLS LAST"""
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, evaluation_id: str) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM council_evaluations WHERE evaluation_id=? ORDER BY id",
                (evaluation_id,),
            ).fetchall()
        return [dict(row) for row in rows]


ledger = AILedger()
