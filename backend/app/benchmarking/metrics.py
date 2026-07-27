"""
metrics.py

Pure calculation helpers for ArmPilot's benchmarking module.
No I/O, no side effects — these functions take numbers in and return
numbers out, which makes them trivial to unit test and safe to call
from benchmark_runner.py, the FastAPI routes, or a notebook.

Includes:
  - Dashboard helpers: calculate_improvement, summarize_run (before/after charts)
  - Runtime helper: BenchmarkMetrics dataclass (single-model trial samples)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TypedDict


class ImprovementResult(TypedDict):
    baseline_speed: float
    optimized_speed: float
    improvement: float


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


def calculate_improvement(baseline_speed: float, optimized_speed: float) -> ImprovementResult:
    """
    Calculate the percentage improvement between a baseline and an
    optimized measurement (e.g. tokens/sec, ms latency, MB memory).
    """
    if baseline_speed <= 0:
        raise ValueError("baseline_speed must be greater than 0 to compute a percentage improvement")

    improvement = ((optimized_speed - baseline_speed) / baseline_speed) * 100

    return {
        "baseline_speed": baseline_speed,
        "optimized_speed": optimized_speed,
        "improvement": round(improvement, 2),
    }


def calculate_memory_reduction(baseline_mb: float, optimized_mb: float) -> ImprovementResult:
    """
    Same idea as calculate_improvement, but for metrics where LOWER is
    better (memory usage, latency, power draw).
    """
    if baseline_mb <= 0:
        raise ValueError("baseline_mb must be greater than 0 to compute a percentage reduction")

    reduction = ((baseline_mb - optimized_mb) / baseline_mb) * 100

    return {
        "baseline_speed": baseline_mb,
        "optimized_speed": optimized_mb,
        "improvement": round(reduction, 2),
    }


def summarize_run(baseline: dict, optimized: dict) -> dict:
    """
    Build the full before/after summary the dashboard's BenchmarkCharts
    component expects, given raw baseline/optimized benchmark records.
    """
    speed = calculate_improvement(
        baseline_speed=baseline["tokens_per_sec"],
        optimized_speed=optimized["tokens_per_sec"],
    )

    memory = None
    if "memory_mb" in baseline and "memory_mb" in optimized:
        memory = calculate_memory_reduction(
            baseline_mb=baseline["memory_mb"],
            optimized_mb=optimized["memory_mb"],
        )

    return {
        "before": baseline,
        "after": optimized,
        "speed_improvement_pct": speed["improvement"],
        "memory_reduction_pct": memory["improvement"] if memory else None,
    }
