"""
FR-4/FR-5: Optimization Engine.
Rule-based decision engine (NOT ML for MVP - transparency matters for demo/judging).
Input: (battery_pct, available_ram_gb, thermal_state, workload_type, user_profile)
Output: (model, quantization, thread_count, context_length, profile)
Owner: Member 2 (secondary: Member 3)
See rules.py for the actual decision table.
"""

from __future__ import annotations

from typing import Any, Dict

from .rules import resolve_rules


def build_optimization_state(
    *,
    battery_pct: float | None,
    available_ram_gb: float | None,
    thermal_state: str | None,
    workload_type: str | None,
    user_profile: str | None,
    current_threads: int | None,
    swap_usage_high: bool | None = None,
) -> Dict[str, Any]:
    return {
        "battery_pct": battery_pct,
        "available_ram_gb": available_ram_gb,
        "thermal": thermal_state or "nominal",
        "workload": workload_type or "chat",
        "mode": user_profile or "automatic",
        "current_threads": current_threads or 8,
        "swap_usage_high": bool(swap_usage_high),
    }


def optimize(state: Dict[str, Any], max_cores: int) -> Dict[str, Any]:
    return resolve_rules(state, max_cores)
