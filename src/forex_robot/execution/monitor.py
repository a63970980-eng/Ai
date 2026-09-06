from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class ReconciliationIssue:
    kind: str
    key: str
    detail: str

@dataclass(frozen=True)
class ReconciliationResult:
    healthy: bool
    issues: tuple[ReconciliationIssue, ...]


def reconcile_positions(local: Iterable[dict], broker: Iterable[dict], unit_tolerance: float = 1e-9) -> ReconciliationResult:
    def normalize(items: Iterable[dict]) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for p in items:
            key = str(p.get("position_id") or p.get("client_order_id") or f"{str(p.get('symbol','')).upper()}:{str(p.get('side','')).lower()}")
            out[key] = p
        return out

    left, right = normalize(local), normalize(broker)
    issues: list[ReconciliationIssue] = []
    for key in sorted(left.keys() - right.keys()):
        issues.append(ReconciliationIssue("missing_broker_position", key, "local position is absent at broker"))
    for key in sorted(right.keys() - left.keys()):
        issues.append(ReconciliationIssue("unexpected_broker_position", key, "broker position is absent locally"))
    for key in sorted(left.keys() & right.keys()):
        l, r = left[key], right[key]
        if str(l.get("symbol", "")).upper() != str(r.get("symbol", "")).upper():
            issues.append(ReconciliationIssue("symbol_mismatch", key, "position symbols differ"))
        if str(l.get("side", "")).lower() != str(r.get("side", "")).lower():
            issues.append(ReconciliationIssue("side_mismatch", key, "position sides differ"))
        lu, ru = float(l.get("units", 0)), float(r.get("units", 0))
        if abs(lu - ru) > unit_tolerance:
            issues.append(ReconciliationIssue("units_mismatch", key, f"local={lu} broker={ru}"))
    return ReconciliationResult(not issues, tuple(issues))


def execution_health(connected: bool, last_error: str | None = None, rejected_orders: int = 0) -> dict[str, object]:
    return {
        "connected": bool(connected),
        "healthy": bool(connected) and not last_error,
        "last_error": last_error,
        "rejected_orders": int(rejected_orders),
    }
