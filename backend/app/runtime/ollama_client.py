"""
Wraps the Ollama API: model pull, load, switch, generate.
Owner: Member 3 (secondary: Member 1)
RISK: cold model switches cause latency spikes. Pre-warm/pre-pull all demo models
before any live demo. See docs/SCHEDULE.md Day 2 validation task.
"""
