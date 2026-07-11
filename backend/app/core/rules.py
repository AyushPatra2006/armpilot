"""
Explicit rule table for the optimization engine. Kept separate from optimization_engine.py
so the decision logic is easy to read, demo, and explain live to judges.

Example rules (expand as needed):
- battery < 20%                -> profile = battery_saver
- available_ram_gb < 2         -> reduce context_length, lower thread_count
- workload == "coding"         -> increase context_length, prefer coding-tuned model
- workload == "long_context"   -> prefer smaller quantization (e.g. INT4), larger context_length
"""
