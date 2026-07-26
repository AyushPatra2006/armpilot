"""
FR-1: Device Detection.
Detects device model, CPU/GPU cores, Neural Engine availability, total/available memory,
swap usage, battery %, charging status.
Owner: Member 1 (secondary: Member 4)
NOTE: battery/thermal on macOS needs `pmset -g batt` and/or `powermetrics` (may need sudo) -
psutil alone is NOT sufficient on Apple Silicon. Validate this FIRST (Day 1-2).
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import psutil


@dataclass
class HardwareInfo:
    device_model: str
    architecture: str
    cpu_cores: int
    logical_cores: int
    total_ram_gb: float
    available_ram_gb: float
    swap_usage_gb: float
    battery_pct: Optional[float]
    charging: Optional[bool]
    thermal_state: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _battery_info() -> tuple[Optional[float], Optional[bool]]:
    try:
        output = subprocess.check_output(["pmset", "-g", "batt"], text=True)
    except Exception:
        return None, None
    pct = None
    charging = None
    if "%" in output:
        for token in output.replace(";", " ").split():
            if token.endswith("%"):
                try:
                    pct = float(token.rstrip("%"))
                except ValueError:
                    pass
                break
    charging = "charging" in output.lower()
    return pct, charging


def detect_hardware() -> HardwareInfo:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    pct, charging = _battery_info()
    return HardwareInfo(
        device_model=platform.machine(),
        architecture=platform.processor() or platform.machine(),
        cpu_cores=psutil.cpu_count(logical=False) or 1,
        logical_cores=psutil.cpu_count(logical=True) or 1,
        total_ram_gb=round(vm.total / (1024**3), 2),
        available_ram_gb=round(vm.available / (1024**3), 2),
        swap_usage_gb=round(swap.used / (1024**3), 2),
        battery_pct=pct,
        charging=charging,
        thermal_state="nominal",
    )
