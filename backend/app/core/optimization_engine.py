"""
FR-4/FR-5: Optimization Engine.
Rule-based decision engine (NOT ML for MVP - transparency matters for demo/judging).
Input: (battery_pct, available_ram_gb, thermal_state, workload_type, user_profile)
Output: (model, quantization, thread_count, context_length, profile)
Owner: Member 2 (secondary: Member 3)
See rules.py for the actual decision table.

This module is a thin wrapper around rules.resolve_rules(): it adapts hardware +
system + workload inputs into the state dict the rule table expects, then adds
human-readable reasoning for judges/demo.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .rules import resolve_rules


def generate_reasoning(
    hardware: Dict[str, Any],
    system: Dict[str, Any],
    workload: str,
    mode: str,
    config: Dict[str, Any],
) -> List[str]:
    """
    Build plain-English explanations of why this configuration was chosen.

    Kept separate from the rule table so judges can hear the "why" without
    digging through priority math in rules.py.
    """
    reasons: List[str] = []

    # --- Device / RAM ---
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

    # --- Manual profile (short-circuit narrative) ---
    if mode and mode != "automatic":
        reasons.append(f"Manual '{mode}' profile selected by user")
        if config.get("model"):
            reasons.append(f"Baseline model set to {config['model']}")
        if config.get("quant"):
            reasons.append(f"{config['quant']} selected to reduce memory footprint")
        if config.get("extra_flag"):
            reasons.append(f"Extra runtime flag applied: {config['extra_flag']}")
        return reasons

    # --- Battery ---
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

    # --- Memory / swap ---
    available_ram = system.get("available_ram_gb")
    if available_ram is not None and available_ram < 2:
        reasons.append(
            f"Only {available_ram}GB available RAM — reduced model/context for memory safety"
        )
    if system.get("swap_usage_high"):
        reasons.append("High swap usage detected — memory optimization triggered")

    # --- Thermal ---
    thermal = system.get("thermal")
    if thermal == "hot":
        reasons.append("Thermal state is hot — thread count reduced to cool the device")
    elif thermal == "warm":
        reasons.append("Thermal state is warm — lightly throttling threads")

    # --- Workload / model selection ---
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

    # --- Quantization ---
    quant = config.get("quant")
    if quant:
        reasons.append(f"{quant} selected to reduce memory footprint")

    # --- Profile label ---
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
    Combine hardware detection + system monitoring + workload into an optimized
    Ollama configuration. Does not call Ollama or mutate device state — decision
    only.

    Args:
        hardware: e.g. {"device": "...", "cpu": "...", "cores": 8, "ram_gb": 16}
        system: e.g. {"battery_pct", "charging", "available_ram_gb", "thermal",
            "swap_usage_high", optional "current_threads"}
        workload: workload class string (chat, coding, long_context, ...)
        mode: "automatic" or a named baseline ("speed", "quality", "battery_saver")

    Returns:
        Dict with model, quant, threads, context_length, profile, optional
        extra_flag, and reasoning (list of human-readable strings).
    """
    if "cores" not in hardware:
        raise ValueError("hardware must include 'cores' (max CPU cores)")

    max_cores = int(hardware["cores"])
    current_threads = system.get("current_threads", max_cores)

    state: Dict[str, Any] = {
        "mode": mode,
        "battery_pct": system.get("battery_pct"),
        "charging": system.get("charging", False),
        "available_ram_gb": system.get("available_ram_gb"),
        "thermal": system.get("thermal"),
        "swap_usage_high": system.get("swap_usage_high", False),
        "workload": workload,
        "current_threads": current_threads,
    }

    config = resolve_rules(state, max_cores=max_cores)
    reasoning = generate_reasoning(hardware, system, workload, mode, config)

    result = dict(config)
    result["reasoning"] = reasoning
    return result
