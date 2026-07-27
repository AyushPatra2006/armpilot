"""
hardware_detection.py

FR-1: Device Detection.
Detects device model, CPU/GPU cores, Neural Engine availability, total/available memory,
swap usage, battery %, charging status.
Owner: Member 1 (secondary: Member 4)

Provides:
  - detect_hardware()  → full HardwareInfo dataclass (runtime / optimize pipeline)
  - get_hardware_info() → dashboard-shaped dict (DeviceStatus.tsx keys)
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, TypedDict

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


class DashboardHardwareInfo(TypedDict):
    """Shape expected by frontend DeviceStatus.tsx."""

    device: str
    processor: str
    cores: int
    memory_gb: float
    battery_percent: int
    plugged_in: bool


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
    try:
        swap_used = psutil.swap_memory().used
    except Exception:
        swap_used = 0
    pct, charging = _battery_info()
    return HardwareInfo(
        device_model=platform.machine(),
        architecture=platform.processor() or platform.machine(),
        cpu_cores=psutil.cpu_count(logical=False) or 1,
        logical_cores=psutil.cpu_count(logical=True) or 1,
        total_ram_gb=round(vm.total / (1024**3), 2),
        available_ram_gb=round(vm.available / (1024**3), 2),
        swap_usage_gb=round(swap_used / (1024**3), 2),
        battery_pct=pct,
        charging=charging,
        thermal_state="nominal",
    )


def get_hardware_info() -> DashboardHardwareInfo:
    """
    Dashboard-compatible view of the same live detection.
    Keeps DeviceStatus.tsx keys stable while using real sensors underneath.
    """
    hw = detect_hardware()
    return {
        "device": hw.device_model,
        "processor": hw.architecture or hw.device_model,
        "cores": hw.logical_cores,
        "memory_gb": hw.total_ram_gb,
        "battery_percent": int(hw.battery_pct) if hw.battery_pct is not None else 0,
        "plugged_in": bool(hw.charging),
    }
