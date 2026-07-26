"""
FastAPI routes: /device, /monitor, /optimize, /benchmark, /log.
Owner: Member 2 (secondary: Member 3)
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.benchmarking.benchmark_runner import BenchmarkRunner
from app.core.hardware_detection import detect_hardware
from app.core.optimization_engine import build_optimization_state, optimize
from app.core.workload_classifier import classify_workload
from app.logging.optimization_log import get_recent_logs, record_decision
from app.runtime.model_manager import ModelManager

router = APIRouter(prefix="/api", tags=["armpilot"])
runtime_manager = ModelManager()
benchmark_runner = BenchmarkRunner()


class RunRequest(BaseModel):
    model: str
    prompt: str
    settings: dict = Field(default_factory=dict)


class OptimizeRequest(BaseModel):
    prompt: str
    mode: str = "automatic"


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


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
    return {"hardware": hardware.as_dict(), "workload": workload.__dict__, "decision": decision}


@router.post("/run")
def run_route(payload: RunRequest) -> dict:
    try:
        result = runtime_manager.run_inference(payload.prompt, payload.settings | {"model": payload.model})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
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
    run = benchmark_runner.run_benchmark(payload.model, payload.prompt, payload.settings)
    return run
