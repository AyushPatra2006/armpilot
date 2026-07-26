"""
FR-6: Optimization Log.
Records every optimization decision (timestamp, detected conditions, action taken, estimated impact)
to SQLite. This feeds the dashboard's decision history view.
Owner: Member 2 (secondary: Member 4)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

_LOG: List[Dict[str, Any]] = []


def record_decision(entry: Dict[str, Any]) -> Dict[str, Any]:
    stored = dict(entry)
    stored.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    _LOG.append(stored)
    return stored


def get_recent_logs(limit: int = 20) -> List[Dict[str, Any]]:
    return list(reversed(_LOG[-limit:]))
