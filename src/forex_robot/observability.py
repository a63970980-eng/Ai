from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


@dataclass(frozen=True)
class RuntimeSnapshot:
    started_at: str
    events: int
    errors: int
    blocked_trades: int
    paper_orders: int


class RuntimeMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._started = datetime.now(timezone.utc)
        self._counters: Counter[str] = Counter()

    def inc(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] += value

    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            return RuntimeSnapshot(
                started_at=self._started.isoformat(),
                events=sum(self._counters.values()),
                errors=self._counters["errors"],
                blocked_trades=self._counters["blocked_trades"],
                paper_orders=self._counters["paper_orders"],
            )


metrics = RuntimeMetrics()
