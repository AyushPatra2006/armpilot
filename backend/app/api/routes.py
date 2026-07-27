"""
routes.py

FastAPI router for ArmPilot — merges dashboard endpoints (hardware / logs /
comparison benchmark) with runtime integration endpoints (device / optimize /
run / single-model benchmark / log).

This router only orchestrates — it calls into core/, logging/, runtime/, and
benchmarking/ modules and shapes their output into HTTP responses.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.benchmarking.benchmark_runner import BenchmarkRunner
from app.core.hardware_detection import detect_hardware, get_hardware_info
from app.core.optimization_engine import build_optimization_state, optimize
from app.core.workload_classifier import classify_workload
from app.logging.optimization_log import get_recent_logs, record_decision
from app.runtime.model_manager import ModelManager

router = APIRouter(prefix="/api", tags=["armpilot"])

runtime_manager = ModelManager()
# Dashboard comparison path stays mock-friendly for live demos; runtime
# POST /benchmark uses the same runner's real ModelManager path.
comparison_runner = BenchmarkRunner(mock=True)
benchmark_runner = BenchmarkRunner(mock=False, runtime=runtime_manager)

# Demo-friendly log entries when nothing has been recorded yet — keeps the
# dashboard populated for judges even before the first /optimize call.
_DEMO_LOGS: List[Dict[str, Any]] = [
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


class RunRequest(BaseModel):
    model: str
    prompt: str
    settings: dict = Field(default_factory=dict)


class OptimizeRequest(BaseModel):
    prompt: str
    mode: str = "automatic"


def _to_dashboard_log(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Map a recorded decision into the OptimizationLog.tsx shape."""
    decision = entry.get("decision") or {}
    workload = (entry.get("input") or {}).get("workload")
    model = decision.get("model") or "unknown"
    profile = decision.get("profile") or "automatic"
    quant = decision.get("quant") or decision.get("quantization") or ""
    change = f"→ {profile}"
    if quant:
        change = f"{quant} / {profile}"
    reason = entry.get("event") or "optimize"
    if workload:
        reason = f"{reason} ({workload})"
    return {
        "timestamp": str(entry.get("timestamp", ""))[:19].replace("T", " "),
        "model": model,
        "change": change,
        "reason": reason,
        "expected_impact": (
            f"threads={decision.get('threads')}, "
            f"ctx={decision.get('context_length')}"
        ),
    }


# ---------------------------------------------------------------------------
# Shared / dashboard endpoints
# ---------------------------------------------------------------------------
@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/hardware")
def get_hardware() -> dict:
    """Dashboard DeviceStatus — live detection mapped to UI keys."""
    return get_hardware_info()


@router.get("/logs")
def get_logs() -> list:
    """Dashboard OptimizationLog — decision history in UI shape."""
    recent = get_recent_logs()
    if not recent:
        return list(_DEMO_LOGS)
    return [_to_dashboard_log(entry) for entry in recent]


@router.get("/benchmark")
def get_benchmark() -> dict:
    """Dashboard BenchmarkCharts — mock before/after comparison."""
    return comparison_runner.run_comparison_benchmark(
        prompt="Summarize this 200-page report.",
        baseline_model="Qwen3 8B INT8",
        optimized_model="Qwen3 8B INT4",
    )


# ---------------------------------------------------------------------------
# Runtime / optimization endpoints (from main)
# ---------------------------------------------------------------------------
@router.get("/device")
def device() -> dict:
    return detect_hardware().as_dict()


@router.get("/log")
def log() -> dict:
    return {"items": get_recent_logs()}


@router.post("/optimize")
def optimize_route(payload: OptimizeRequest) -> dict:
    hardware = detect_hardware()
    workload = classify_workload(payload.prompt)
    state = build_optimization_state(
        battery_pct=hardware.battery_pct,
        available_ram_gb=hardware.available_ram_gb,
        thermal_state=hardware.thermal_state,
        workload_type=workload.label,
        user_profile=payload.mode,
        current_threads=hardware.logical_cores,
        swap_usage_high=hardware.swap_usage_gb > 0.5,
    )
    decision = optimize(state, hardware.logical_cores)
    decision["workload"] = workload.label
    decision["workload_reason"] = workload.reason
    record_decision({"event": "optimize", "input": state, "decision": decision})
    return {
        "hardware": hardware.as_dict(),
        "workload": workload.__dict__,
        "decision": decision,
    }


@router.post("/run")
def run_route(payload: RunRequest) -> dict:
    try:
        result = runtime_manager.run_inference(
            payload.prompt, payload.settings | {"model": payload.model}
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "response": result.response,
        "tokens_generated": result.tokens_generated,
        "latency": result.latency,
        "tokens_per_second": result.tokens_per_second,
        "time_to_first_token": result.time_to_first_token,
        "model": result.model,
    }


@router.post("/benchmark")
def benchmark_route(payload: RunRequest) -> dict:
    """Runtime single-model benchmark (distinct from GET comparison above)."""
    return benchmark_runner.run_benchmark(payload.model, payload.prompt, payload.settings)
