"""
FR-1: Device Detection.
Detects device model, CPU/GPU cores, Neural Engine availability, total/available memory,
swap usage, battery %, charging status.
Owner: Member 1 (secondary: Member 4)
NOTE: battery/thermal on macOS needs `pmset -g batt` and/or `powermetrics` (may need sudo) -
psutil alone is NOT sufficient on Apple Silicon. Validate this FIRST (Day 1-2).
"""

  
import platform
import re
import subprocess
from typing import Dict, Optional
import psutil
_MODEL_NAME_RE = re.compile(r"Model Name:\s*(.+)", re.IGNORECASE)
_CHIP_RE = re.compile(r"Chip:\s*(.+)", re.IGNORECASE)


def _run_command(cmd: list[str], timeout: float = 5.0) -> Optional[str]:
    """
    Run a shell command and return its stdout, or None on any failure.
    Never raises - callers (including other team members' code) depend on
    this failing silently rather than crashing their process.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except (OSError, subprocess.SubprocessError, ValueError):
        return None

    
def _parse_system_profiler(output: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract model name and chip from `system_profiler SPHardwareDataType`
    text output. This is parsing human-readable text, not a stable API -
    field order/wording could shift across macOS versions, so treat this
    as best-effort rather than guaranteed.
    """
    model_name = None
    chip = None
    for line in output.splitlines():
        if model_name is None:
            match = _MODEL_NAME_RE.search(line)
            if match:
                model_name = match.group(1).strip()
        if chip is None:
            match = _CHIP_RE.search(line)
            if match:
                chip = match.group(1).strip()
        if model_name and chip:
            break
    return model_name, chip


def _build_device_name(model_name: Optional[str], chip: Optional[str]) -> str:
    """
    Combine model + chip into a single display string (e.g. "MacBook Air M1").
    Falls back to whichever piece is available, or "Unknown Mac" if neither
    parsed successfully - a generic fallback, not a fabricated real-looking
    device name, so downstream consumers can tell detection failed.
    """
    if model_name and chip:
        chip_suffix = chip.removeprefix("Apple ").strip()
        return f"{model_name} {chip_suffix}"
    if model_name:
        return model_name
    if chip:
        return chip
    return "Unknown Mac"


def _get_os_string() -> str:
    """
    Returns a human-readable OS string, e.g. "macOS 13.4".
    Falls back to "Unknown" on any failure - never raises, since callers
    depend on this not crashing their process.
    """
    try:
        if platform.system() == "Darwin":
            version, _, _ = platform.mac_ver()
            if version:
                return f"macOS {version}"
            return "macOS"
        system = platform.system()
        return system if system else "Unknown"
    except Exception:
        return "Unknown"


def get_hardware_info() -> dict:
    """
    FR-1 main entry point: static device info that does not change during
    a running session (device, cpu, architecture, cores, ram, os).
    Safe to call once and cache - no need to re-run this every poll cycle.
    """
    model_name: Optional[str] = None
    chip: Optional[str] = None
    profiler_output = _run_command(["system_profiler", "SPHardwareDataType"])
    if profiler_output:
        model_name, chip = _parse_system_profiler(profiler_output)
    try:
        architecture = platform.machine() or "Unknown"
    except Exception:
        architecture = "Unknown"
    try:
        cores = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 0
    except Exception:
        cores = 0
    try:
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        ram_gb = 0.0
    return {
        "device": _build_device_name(model_name, chip),
        "cpu": chip if chip else "Unknown",
        "architecture": architecture,
        "cores": cores,
        "ram_gb": ram_gb,
        "os": _get_os_string(),
    } 
