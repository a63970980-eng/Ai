from __future__ import annotations
from datetime import datetime, timezone
from enum import StrEnum

class Session(StrEnum):
    ASIA='asia'; LONDON='london'; NEW_YORK='new_york'; OVERLAP='london_new_york_overlap'; OFF='off'

def session_at(ts: datetime) -> Session:
    h=ts.astimezone(timezone.utc).hour
    if 13 <= h < 16: return Session.OVERLAP
    if 7 <= h < 13: return Session.LONDON
    if 16 <= h < 22: return Session.NEW_YORK
    if 0 <= h < 7: return Session.ASIA
    return Session.OFF

def session_score(ts: datetime) -> float:
    return {Session.OVERLAP:100.0, Session.LONDON:90.0, Session.NEW_YORK:90.0, Session.ASIA:60.0, Session.OFF:20.0}[session_at(ts)]
