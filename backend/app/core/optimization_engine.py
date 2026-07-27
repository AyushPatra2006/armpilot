"""
FR-4/FR-5: Optimization Engine.
Rule-based decision engine (NOT ML for MVP - transparency matters for demo/judging).
Input: (battery_pct, available_ram_gb, thermal_state, workload_type, user_profile)
Output: (model, quantization, thread_count, context_length, profile)
Owner: Member 2 (secondary: Member 3)
See rules.py for the actual decision table.

Thin adapters around rules.resolve_rules() used by the /api/optimize route
and any callers that already speak in hardware/system dicts.
"""

from __future__ import annotations

from typing import Any, Dict, List

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
    """Map route/sensor fields into the state dict expected by resolve_rules()."""
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
    """Resolve a pre-built state dict into an inference configuration."""
    return resolve_rules(state, max_cores)


def generate_reasoning(
    hardware: Dict[str, Any],
    system: Dict[str, Any],
    workload: str,
    mode: str,
    config: Dict[str, Any],
) -> List[str]:
    """Human-readable explanations for judges / dashboard."""
    reasons: List[str] = []

    ram_gb = hardware.get("ram_gb")
    device = hardware.get("device")
    if device and ram_gb is not None:
        reasons.append(f"{device} with {ram_gb}GB RAM detected")
    elif ram_gb is not None:
        reasons.append(f"{ram_gb}GB RAM detected")
    elif device:
        reasons.append(f"Device detected: {device}")

    cores = hardware.get("cores")
    if cores is not None:
        reasons.append(f"{cores} CPU cores available for thread scheduling")

    if mode and mode != "automatic":
        reasons.append(f"Manual '{mode}' profile selected by user")
        if config.get("model"):
            reasons.append(f"Baseline model set to {config['model']}")
        if config.get("quant"):
            reasons.append(f"{config['quant']} selected to reduce memory footprint")
        if config.get("extra_flag"):
            reasons.append(f"Extra runtime flag applied: {config['extra_flag']}")
        return reasons

    battery_pct = system.get("battery_pct")
    charging = bool(system.get("charging", False))
    if battery_pct is not None and battery_pct < 20 and not charging:
        reasons.append(
            f"Battery at {battery_pct}% and unplugged — battery optimization enabled"
        )
        if config.get("profile") == "battery_saver":
            reasons.append("Switched to battery_saver profile (smaller model, fewer threads)")
    elif battery_pct is not None and battery_pct < 20 and charging:
        reasons.append(
            f"Battery at {battery_pct}% but charging — battery_saver not required"
        )

    available_ram = system.get("available_ram_gb")
    if available_ram is not None and available_ram < 2:
        reasons.append(
            f"Only {available_ram}GB available RAM — reduced model/context for memory safety"
        )
    if system.get("swap_usage_high"):
        reasons.append("High swap usage detected — memory optimization triggered")

    thermal = system.get("thermal")
    if thermal == "hot":
        reasons.append("Thermal state is hot — thread count reduced to cool the device")
    elif thermal == "warm":
        reasons.append("Thermal state is warm — lightly throttling threads")

    workload_key = (workload or "chat").lower()
    model = config.get("model")
    context_length = config.get("context_length")
    if workload_key == "coding":
        reasons.append(
            f"Coding workload selected {model} with context_length={context_length}"
        )
    elif workload_key == "long_context":
        reasons.append(
            f"Long-context workload selected {model} with context_length={context_length}"
        )
    elif model:
        reasons.append(f"Workload '{workload_key}' resolved to model {model}")

    quant = config.get("quant")
    if quant:
        reasons.append(f"{quant} selected to reduce memory footprint")

    profile = config.get("profile")
    if profile and profile != "automatic":
        reasons.append(f"Active profile: {profile}")
    elif profile == "automatic":
        reasons.append("Configuration assembled automatically from matching rules")

    if config.get("extra_flag"):
        reasons.append(f"Extra runtime flag applied: {config['extra_flag']}")

    return reasons


def optimize_configuration(
    hardware: Dict[str, Any],
    system: Dict[str, Any],
    workload: str = "chat",
    mode: str = "automatic",
) -> Dict[str, Any]:
    """
    High-level entry point: hardware + system + workload → config + reasoning.
    Used by tests and any caller that prefers dict inputs over keyword state building.
    """
    if "cores" not in hardware:
        raise ValueError("hardware must include 'cores' (max CPU cores)")

    max_cores = int(hardware["cores"])
    current_threads = system.get("current_threads", max_cores)

    state = build_optimization_state(
        battery_pct=system.get("battery_pct"),
        available_ram_gb=system.get("available_ram_gb"),
        thermal_state=system.get("thermal"),
        workload_type=workload,
        user_profile=mode,
        current_threads=current_threads,
        swap_usage_high=system.get("swap_usage_high", False),
    )

    config = optimize(state, max_cores=max_cores)
    result = dict(config)
    result["reasoning"] = generate_reasoning(hardware, system, workload, mode, config)
    return result
