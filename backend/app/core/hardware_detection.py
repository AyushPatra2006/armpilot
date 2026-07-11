"""
FR-1: Device Detection.
Detects device model, CPU/GPU cores, Neural Engine availability, total/available memory,
swap usage, battery %, charging status.
Owner: Member 1 (secondary: Member 4)
NOTE: battery/thermal on macOS needs `pmset -g batt` and/or `powermetrics` (may need sudo) -
psutil alone is NOT sufficient on Apple Silicon. Validate this FIRST (Day 1-2).
"""
