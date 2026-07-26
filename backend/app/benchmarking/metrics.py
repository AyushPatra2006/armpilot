"""
metrics.py

Pure calculation helpers for ArmPilot's benchmarking module.
No I/O, no side effects — these functions take numbers in and return
numbers out, which makes them trivial to unit test and safe to call
from benchmark_runner.py, the FastAPI routes, or a notebook.
"""

from __future__ import annotations

from typing import TypedDict


class ImprovementResult(TypedDict):
    baseline_speed: float
    optimized_speed: float
    improvement: float


def calculate_improvement(baseline_speed: float, optimized_speed: float) -> ImprovementResult:
    """
    Calculate the percentage improvement between a baseline and an
    optimized measurement (e.g. tokens/sec, ms latency, MB memory).

    Args:
        baseline_speed: The metric value before optimization.
        optimized_speed: The metric value after optimization.

    Returns:
        A dict shaped like:
            {
                "baseline_speed": 30,
                "optimized_speed": 45,
                "improvement": 50.0
            }

    Raises:
        ValueError: if baseline_speed is 0 or negative, since percentage
            improvement is undefined in that case.

    Example:
        >>> calculate_improvement(30, 45)
        {'baseline_speed': 30, 'optimized_speed': 45, 'improvement': 50.0}
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
    better (memory usage, latency, power draw). Returns a positive
    number when the optimized value is smaller (i.e. an improvement).

    Example:
        >>> calculate_memory_reduction(8000, 5200)
        {'baseline_speed': 8000, 'optimized_speed': 5200, 'improvement': 35.0}
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

    Both `baseline` and `optimized` are dicts like:
        {"model": "Qwen3 INT8", "tokens_per_sec": 30, "memory_mb": 8000}

    Returns a dict ready to be returned directly from the /api/benchmark
    route or dropped into calculate_improvement()'s consumers.
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
