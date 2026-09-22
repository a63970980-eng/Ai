from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class TradeJournalEntry:
    timestamp: datetime
    pair: str
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    units: float
    risk: float
    signal_score: float
    strategy: str
    regime: str
    session: str
    spread: float
    slippage: float
    ai_analysis: str = ""
    result: float = 0.0
    r_multiple: float = 0.0
    exit_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class Journal:
    """Small durable journal with SQLite persistence and an in-memory-safe default.

    Set AI_JOURNAL_DB to a persistent filesystem path in a long-running deployment.
    Serverless filesystems remain instance-local/ephemeral unless backed by external storage.
    """

    def __init__(self, path: str | None = None) -> None:
        configured = path or os.getenv("AI_JOURNAL_DB", "/tmp/ai_trades.sqlite3" if os.getenv("VERCEL") else "data/trades.sqlite3")
        self.path = configured
        self._lock = Lock()
        if configured != ":memory:":
            Path(configured).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(configured, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS trade_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pair TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                units REAL NOT NULL,
                risk REAL NOT NULL,
                signal_score REAL NOT NULL,
                strategy TEXT NOT NULL,
                regime TEXT NOT NULL,
                session TEXT NOT NULL,
                spread REAL NOT NULL,
                slippage REAL NOT NULL,
                ai_analysis TEXT NOT NULL DEFAULT '',
                result REAL NOT NULL DEFAULT 0,
                r_multiple REAL NOT NULL DEFAULT 0,
                exit_reason TEXT NOT NULL DEFAULT ''
            )"""
        )
        self._db.commit()

    def record(self, entry: TradeJournalEntry) -> None:
        with self._lock:
            self._db.execute(
                """INSERT INTO trade_journal
                (timestamp,pair,direction,entry,stop_loss,take_profit,units,risk,signal_score,
                 strategy,regime,session,spread,slippage,ai_analysis,result,r_multiple,exit_reason)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    entry.timestamp.isoformat(), entry.pair, entry.direction, entry.entry,
                    entry.stop_loss, entry.take_profit, entry.units, entry.risk,
                    entry.signal_score, entry.strategy, entry.regime, entry.session,
                    entry.spread, entry.slippage, entry.ai_analysis, entry.result,
                    entry.r_multiple, entry.exit_reason,
                ),
            )
            self._db.commit()

    def all(self, limit: int = 500) -> list[dict[str, Any]]:
        if limit < 1 or limit > 5000:
            raise ValueError("limit must be between 1 and 5000")
        rows = self._db.execute(
            "SELECT * FROM trade_journal ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    def clear(self) -> None:
        with self._lock:
            self._db.execute("DELETE FROM trade_journal")
            self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()
