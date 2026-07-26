"""
Metric collection helpers (tokens/sec, TTFT, memory, CPU, battery, swap).
Owner: Member 1 (secondary: Member 4)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class BenchmarkMetrics:
    tokens_per_second: float
    time_to_first_token: float
    latency: float
    cpu_utilization: float | None = None
    memory_usage_gb: float | None = None
    battery_pct: float | None = None
    swap_usage_gb: float | None = None

    def as_dict(self):
        return asdict(self)
