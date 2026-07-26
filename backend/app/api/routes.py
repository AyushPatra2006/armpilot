"""
routes.py

OWNERSHIP: Drishant (Dashboard + Benchmarking Visualization).

This router only orchestrates — it calls into core/, logging/, and
benchmarking/ modules and shapes their output into HTTP responses. It
deliberately does not contain business logic of its own, so swapping
a stub (hardware_detection, optimization_log) for a real
implementation requires zero changes here.
"""

from fastapi import APIRouter

from app.core.hardware_detection import get_hardware_info
from app.logging.optimization_log import get_recent_logs
from app.benchmarking.benchmark_runner import BenchmarkRunner

router = APIRouter(prefix="/api", tags=["dashboard"])

# mock=True until Rhushil's Ollama runtime integration is wired into
# BenchmarkRunner's ollama_client — see benchmark_runner.py.
_runner = BenchmarkRunner(mock=True)


@router.get("/hardware")
def get_hardware():
    return get_hardware_info()


@router.get("/logs")
def get_logs():
    return get_recent_logs()


@router.get("/benchmark")
def get_benchmark():
    return _runner.run_benchmark(
        prompt="Summarize this 200-page report.",
        baseline_model="Qwen3 8B INT8",
        optimized_model="Qwen3 8B INT4",
    )


@router.get("/health")
def health():
    return {"status": "ok"}
