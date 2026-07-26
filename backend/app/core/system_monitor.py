"""
FR-2: System Monitoring (polls every 5s).
Tracks CPU utilization, memory usage, swap, battery level, thermal state, running apps.
Owner: Member 1 (secondary: Member 4)

NOTE: thermal_pressure requires a per-machine NOPASSWD sudoers rule for
powermetrics (see README/team docs for setup command). Without it, this
field will always return None - that's expected, not a bug.
"""
import re
import subprocess
from typing import Optional
import psutil
_BATTERY_PERCENT_RE = re.compile(r"(\d+)%")
_THERMAL_PRESSURE_RE = re.compile(r"Current pressure level:\s*(\w+)", re.IGNORECASE)


def _run_command(cmd: list[str], timeout: float = 5.0) -> Optional[str]:
    """
    Run a shell command and return its stdout, or None on any failure.
    Never raises - this gets called every ~5 seconds in a polling loop,
    so it must never crash or hang the caller.
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

    
def _parse_battery(output: str) -> tuple[Optional[int], Optional[bool]]:
    """
    Parses `pmset -g batt` output for battery percent and charging state.
    Reliable, no elevated permissions needed - unlike thermal_pressure below.
    """
    battery_percent: Optional[int] = None
    charging: Optional[bool] = None
    for line in output.splitlines():
        percent_match = _BATTERY_PERCENT_RE.search(line)
        if percent_match is None:
            continue
        battery_percent = int(percent_match.group(1))
        lower_line = line.lower()
        if "discharging" in lower_line:
            charging = False
        elif "not charging" in lower_line:
            charging = False
        elif "charging" in lower_line:
            charging = True
        elif "ac attached" in lower_line:
            charging = True
        break
    return battery_percent, charging


def _parse_thermal_pressure(output: str) -> Optional[str]:
    """
    Parses `powermetrics --samplers thermal` output for the qualitative
    pressure level (Nominal/Fair/Serious/Critical).

    IMPORTANT: Apple Silicon does not expose raw CPU temperature via
    powermetrics - the `smc` sampler that provided this on Intel Macs
    doesn't exist here (confirmed by hand on M1 Air). This pressure level
    is the only thermal signal available - do not attempt to derive a
    temperature number from it.
    """
    match = _THERMAL_PRESSURE_RE.search(output)
    if match is None:
        return None
    return match.group(1)


def get_system_state() -> dict:
    """
    FR-2 main entry point: dynamic system state, safe to call repeatedly
    (e.g. every 5 seconds). Unlike get_hardware_info() in hardware_detection.py,
    nothing here should be cached - these values are expected to change.
    """
    battery_percent: Optional[int] = None
    charging: Optional[bool] = None
    pmset_output = _run_command(["pmset", "-g", "batt"], timeout=3.0)
    if pmset_output:
        battery_percent, charging = _parse_battery(pmset_output)
    try:
        memory_available_gb = round(psutil.virtual_memory().available / (1024**3), 2)
    except Exception:
        memory_available_gb = 0.0
    try:
        cpu_usage_percent = float(psutil.cpu_percent(interval=0.1))
    except Exception:
        cpu_usage_percent = 0.0
    thermal_pressure: Optional[str] = None
    powermetrics_output = _run_command(
        [
            "sudo",
            "-n", # non-interactive: fail instantly instead of prompting for
                  # a password, so this never hangs a 5-second polling loop
            "powermetrics",
            "--samplers",
            "thermal",
            "-i",
            "1000",
            "-n",
            "1",
        ],
        timeout=5.0,
    )
    if powermetrics_output:
        thermal_pressure = _parse_thermal_pressure(powermetrics_output)
    return {
        "battery_percent": battery_percent,
        "charging": charging,
        "memory_available_gb": memory_available_gb,
        "cpu_usage_percent": cpu_usage_percent,
        "thermal_pressure": thermal_pressure,
    }
