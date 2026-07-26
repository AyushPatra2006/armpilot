"""
benchmark_runner.py

Orchestrates a before/after benchmark run and hands the results to
metrics.py for scoring. In the hackathon MVP this can call Ollama
directly; for demo purposes (and to keep judges' laptops from waiting
on a real model load) it also supports a --mock mode that returns
realistic canned numbers so the dashboard always has something to draw.
"""

from __future__ import annotations

import time
import random
from dataclasses import dataclass, asdict
from typing import Optional

from app.benchmarking.metrics import summarize_run


@dataclass
class BenchmarkRecord:
    model: str
    quantization: str
    tokens_per_sec: float
    memory_mb: float
    time_to_first_token_ms: float


class BenchmarkRunner:
    """
    Runs a baseline benchmark, then an optimized benchmark, and returns
    a summary shaped for the frontend's BenchmarkCharts component.
    """

    def __init__(self, ollama_client: Optional[object] = None, mock: bool = True):
        # ollama_client is intentionally untyped here — swap in the real
        # Ollama SDK/HTTP client once Rhushil's runtime integration lands.
        self.ollama_client = ollama_client
        self.mock = mock or ollama_client is None

    def run_benchmark(
        self,
        prompt: str,
        baseline_model: str,
        optimized_model: str,
        n_runs: int = 3,
    ) -> dict:
        """
        Run n_runs generations against the baseline config and the
        optimized config, average the results, and return a summary.
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
        """
        Placeholder for a real Ollama call. Wire this up to
        self.ollama_client once the runtime integration (Rhushil) is
        ready. Should time generation and read memory via psutil.
        """
        start = time.perf_counter()
        # response = self.ollama_client.generate(model=model, prompt=prompt)
        elapsed = time.perf_counter() - start
        tokens_generated = 0  # len(tokenizer.encode(response))
        tokens_per_sec = tokens_generated / elapsed if elapsed > 0 else 0

        return BenchmarkRecord(
            model=model,
            quantization="unknown",
            tokens_per_sec=round(tokens_per_sec, 2),
            memory_mb=0,
            time_to_first_token_ms=0,
        )

    def _mock_run(self, model: str) -> BenchmarkRecord:
        """
        Deterministic-ish demo data. INT4/optimized models get a
        healthy speed boost and a lower memory footprint so the story
        (device -> recommendation -> config -> improvement) is always
        visible even with no GPU/model loaded.
        """
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


if __name__ == "__main__":
    runner = BenchmarkRunner(mock=True)
    result = runner.run_benchmark(
        prompt="Summarize this 200-page report.",
        baseline_model="Qwen3 8B INT8",
        optimized_model="Qwen3 8B INT4",
    )
    import json

    print(json.dumps(result, indent=2))
