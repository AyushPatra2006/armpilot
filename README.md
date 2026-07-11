# ArmPilot

Intelligent runtime optimization for local AI on Arm devices.
See docs/PRD.md for the full spec and docs/SCHEDULE.md for the day-by-day build plan.

## Structure
- backend/   FastAPI service: hardware detection, monitoring, optimization engine, Ollama integration, logging
- frontend/  React/Tailwind dashboard
- data/      SQLite db, benchmark results, logs
- scripts/   setup + benchmarking scripts
- docs/      PRD, schedule, architecture notes
- demo/      demo script + fallback assets
