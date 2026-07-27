"""
benchmark_runner.py

Orchestrates benchmarks for both:
  - Dashboard before/after comparison (mock-friendly for live demos)
  - Runtime single-model trials via ModelManager / Ollama

In the hackathon MVP this can call Ollama directly; for demo purposes
(and to keep judges' laptops from waiting on a real model load) the
comparison path also supports mock mode with realistic canned numbers.
"""

from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass
from statistics import median
from typing import Any, Dict, List, Optional

from app.benchmarking.metrics import BenchmarkMetrics, summarize_run
from app.runtime.model_manager import ModelManager


@dataclass
class BenchmarkRecord:
    model: str
    quantization: str
    tokens_per_sec: float
    memory_mb: float
    time_to_first_token_ms: float


class BenchmarkRunner:
    """
    Dual-mode runner:
      - run_comparison_benchmark(...) → dashboard before/after summary
      - run_benchmark(model, prompt, settings) → runtime trial medians
    """

    def __init__(
        self,
        ollama_client: Optional[object] = None,
        mock: bool = True,
        runtime: Optional[ModelManager] = None,
    ):
        self.ollama_client = ollama_client
        self.mock = mock or ollama_client is None
        self.runtime = runtime or ModelManager()

    # ------------------------------------------------------------------
    # Dashboard: before vs after comparison
    # ------------------------------------------------------------------
    def run_comparison_benchmark(
        self,
        prompt: str,
        baseline_model: str,
        optimized_model: str,
        n_runs: int = 3,
    ) -> dict:
        """
        Run n_runs generations against the baseline config and the
        optimized config, average the results, and return a summary
        shaped for BenchmarkCharts.
        """
        baseline = self._run_config(model=baseline_model, prompt=prompt, n_runs=n_runs)
        optimized = self._run_config(model=optimized_model, prompt=prompt, n_runs=n_runs)
        return summarize_run(baseline=asdict(baseline), optimized=asdict(optimized))

    def _run_config(self, model: str, prompt: str, n_runs: int) -> BenchmarkRecord:
        if self.mock:
            return self._mock_run(model)

        samples = [self._single_real_run(model, prompt) for _ in range(n_runs)]
        return BenchmarkRecord(
            model=model,
            quantization=samples[0].quantization,
            tokens_per_sec=round(sum(s.tokens_per_sec for s in samples) / len(samples), 2),
            memory_mb=round(sum(s.memory_mb for s in samples) / len(samples), 2),
            time_to_first_token_ms=round(
                sum(s.time_to_first_token_ms for s in samples) / len(samples), 2
            ),
        )

    def _single_real_run(self, model: str, prompt: str) -> BenchmarkRecord:
        start = time.perf_counter()
        result = self.runtime.run_inference(prompt, {"model": model})
        elapsed = time.perf_counter() - start
        tokens_per_sec = result.tokens_per_second or (
            result.tokens_generated / elapsed if elapsed > 0 else 0
        )
        return BenchmarkRecord(
            model=model,
            quantization="unknown",
            tokens_per_sec=round(tokens_per_sec, 2),
            memory_mb=0,
            time_to_first_token_ms=round((result.time_to_first_token or 0) * 1000, 2),
        )

    def _mock_run(self, model: str) -> BenchmarkRecord:
        is_optimized = "int4" in model.lower() or "optimized" in model.lower()

        if is_optimized:
            tokens_per_sec = round(random.uniform(42, 48), 1)
            memory_mb = round(random.uniform(4200, 4800), 0)
            ttft_ms = round(random.uniform(180, 220), 0)
            quant = "INT4"
        else:
            tokens_per_sec = round(random.uniform(28, 32), 1)
            memory_mb = round(random.uniform(7800, 8400), 0)
            ttft_ms = round(random.uniform(320, 380), 0)
            quant = "INT8"

        return BenchmarkRecord(
            model=model,
            quantization=quant,
            tokens_per_sec=tokens_per_sec,
            memory_mb=memory_mb,
            time_to_first_token_ms=ttft_ms,
        )

    # ------------------------------------------------------------------
    # Runtime integration: single-model trial runner
    # ------------------------------------------------------------------
    def run_benchmark(
        self,
        model: str,
        prompt: str,
        settings: Dict[str, Any] | None = None,
        trials: int = 1,
    ) -> Dict[str, Any]:
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


if __name__ == "__main__":
    runner = BenchmarkRunner(mock=True)
    result = runner.run_comparison_benchmark(
        prompt="Summarize this 200-page report.",
        baseline_model="Qwen3 8B INT8",
        optimized_model="Qwen3 8B INT4",
    )
    import json

    print(json.dumps(result, indent=2))
