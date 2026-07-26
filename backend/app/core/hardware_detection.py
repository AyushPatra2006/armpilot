"""
hardware_detection.py

OWNERSHIP: Ian (Feature A — Hardware Detection). This is a STUB.

This file exists so app/api/routes.py has something real to import
and the dashboard isn't blocked waiting on hardware detection to land.
Replace get_hardware_info() with real psutil / macOS system API calls
per the PRD (CPU model, cores, RAM, battery, charging state) — keep
the return shape identical, since DeviceStatus.tsx depends on these
exact keys.
"""

from typing import TypedDict


class HardwareInfo(TypedDict):
    device: str
    processor: str
    cores: int
    memory_gb: float
    battery_percent: int
    plugged_in: bool


def get_hardware_info() -> HardwareInfo:
    """
    TODO(Ian): replace with real detection, e.g.:
        psutil.cpu_count(), psutil.virtual_memory(), psutil.sensors_battery()
    """
    return {
        "device": "MacBook Air M3",
        "processor": "Apple M3",
        "cores": 8,
        "memory_gb": 16,
        "battery_percent": 35,
        "plugged_in": False,
    }
