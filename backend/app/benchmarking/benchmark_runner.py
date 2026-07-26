"""
Runs repeated benchmark trials (same task, optimization on vs off) and computes medians.
Metrics: tokens/sec, time-to-first-token, memory usage, CPU utilization, battery draw, swap usage.
Owner: Member 1 (secondary: Member 4)
"""

from __future__ import annotations

from statistics import median
from typing import Any, Dict, List

from app.benchmarking.metrics import BenchmarkMetrics
from app.runtime.model_manager import ModelManager


class BenchmarkRunner:
    def __init__(self) -> None:
        self.runtime = ModelManager()

    def run_benchmark(self, model: str, prompt: str, settings: Dict[str, Any] | None = None, trials: int = 1) -> Dict[str, Any]:
        settings = settings or {}
        samples: List[BenchmarkMetrics] = []
        for _ in range(max(1, trials)):
            result = self.runtime.run_inference(prompt, {"model": model, **settings})
            samples.append(
                BenchmarkMetrics(
                    tokens_per_second=result.tokens_per_second,
                    time_to_first_token=result.time_to_first_token,
                    latency=result.latency,
                )
            )
        return {
            "model": model,
            "prompt": prompt,
            "trials": trials,
            "median": {
                "tokens_per_second": median([s.tokens_per_second for s in samples]),
                "time_to_first_token": median([s.time_to_first_token for s in samples]),
                "latency": median([s.latency for s in samples]),
            },
            "samples": [s.as_dict() for s in samples],
        }
