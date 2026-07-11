"""
FR-4/FR-5: Optimization Engine.
Rule-based decision engine (NOT ML for MVP - transparency matters for demo/judging).
Input: (battery_pct, available_ram_gb, thermal_state, workload_type, user_profile)
Output: (model, quantization, thread_count, context_length, profile)
Owner: Member 2 (secondary: Member 3)
See rules.py for the actual decision table.
"""
