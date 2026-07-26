"""
optimization_log.py

OWNERSHIP: Ayush / Rhushil (Optimization Engine + Runtime Integration).
This is a STUB.

Replace get_recent_logs() with real entries written whenever
core/optimization_engine.py makes a decision (quantization change,
thread count change, model switch, etc). Keep the return shape
identical — OptimizationLog.tsx depends on these exact keys.

In the real implementation this will likely read from db/models.py
(SQLite) rather than returning a hardcoded list.
"""

from typing import TypedDict, List


class LogEntry(TypedDict):
    timestamp: str
    model: str
    change: str
    reason: str
    expected_impact: str


def get_recent_logs() -> List[LogEntry]:
    """
    TODO(Ayush/Rhushil): read from the real optimization engine /
    db/models.py once decisions are being persisted.
    """
    return [
        {
            "timestamp": "10:32 AM",
            "model": "Qwen3 8B",
            "change": "INT8 → INT4",
            "reason": "Reduce memory usage",
            "expected_impact": "Lower latency, -35% power",
        },
        {
            "timestamp": "10:41 AM",
            "model": "Qwen3 8B",
            "change": "Thread count 8 → 10",
            "reason": "Coding workload detected",
            "expected_impact": "+24% throughput",
        },
    ]
