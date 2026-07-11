# ArmPilot PRD (v2)

## Intelligent Runtime Optimization for Local AI on Arm Devices

> This is the working PRD. Changes from v1 are aimed at making the project buildable in
> a 3-week hackathon timeline with a demo that holds up under live conditions. See
> `docs/SCHEDULE.md` for the day-by-day plan that implements this spec.

---

## Project Name

**ArmPilot**

## Tagline

> The intelligent copilot for local AI on Arm devices.

ArmPilot automatically optimizes local AI workloads by dynamically selecting the best
model configuration based on hardware capabilities, system state, and workload
characteristics. Users focus on using AI; ArmPilot handles performance optimization.

---

## Problem Statement

Local AI has become increasingly popular due to privacy, offline capability, reduced
cloud costs, and lower latency. However, running local AI models remains difficult for
most users, who are required to manually configure model selection, quantization level,
thread counts, context lengths, performance profiles, and resource allocation — with
little understanding of these parameters or their impact.

As a result: devices consume excessive memory, battery life suffers, inference is
slower than necessary, and users spend significant time experimenting with settings.
Current local AI tools expose optimization settings but rarely automate them.

---

## Vision

ArmPilot acts as an intelligent optimization layer between local AI applications and
local inference runtimes. It continuously monitors device capabilities, resource
availability, task complexity, and user preferences, and automatically selects the
optimal configuration.

> Deliver the best possible AI experience for the current situation.

Local AI today resembles PC gaming in the early 2000s — users must manually tune dozens
of settings. ArmPilot aims to become the **NVIDIA GeForce Experience for local AI**.

---

## Target Users

**Primary:** Developers using local LLMs, students, researchers, AI enthusiasts,
privacy-conscious users.

**Secondary:** Enterprises using local inference, edge AI developers, teams working with
confidential data.

---

## Supported Platforms

**Hackathon MVP:** Apple Silicon Macs (M1 / M2 / M3 / M4)

**Future Expansion:** Snapdragon X Elite devices, Raspberry Pi, Arm64 Linux, Android

## Supported AI Runtimes

**MVP:** Ollama only. (Deliberately scoped down — multi-runtime support is a fast way to
burn hackathon time without adding demo value.)

**Future:** llama.cpp, LM Studio, Open WebUI, vLLM, Jan

---

## Core Product Concept

User submits an AI request → ArmPilot evaluates device capabilities, current resource
availability, workload complexity, and user preferences → ArmPilot automatically selects
model, quantization level, thread count, context length, and optimization profile.

## Example Workflow

**User Device:** MacBook Air M3, 16GB RAM, battery 24%, running on battery power

**User Request:** "Summarize a 250-page research paper."

**Detected:** long context workload, low battery condition, limited available memory

**Selected:** Model: Qwen 3 8B INT4 · Threads: 8 · Context Length: 16k · Profile: Battery
Optimized

**Reported improvement:** measured against a same-task, same-device baseline (see
Benchmarking Methodology below) — not an assumed percentage.

---

## Functional Requirements

### FR-1 Device Detection
Detects device model, CPU architecture, CPU/GPU core count, Neural Engine availability,
total/available memory, swap usage, battery percentage, charging status.

> **Implementation note:** `psutil` alone does not expose battery or thermal state on
> Apple Silicon. Use `pmset -g batt` for battery, and `powermetrics` (may require elevated
> permissions) for thermal/power data. Validate this on the actual demo machine on Day 1 —
> see risk register below.

### FR-2 System Monitoring
Continuously monitors CPU utilization, memory usage, swap usage, battery level, thermal
state, running applications. Polling interval: every 5 seconds.

### FR-3 Workload Classification
Classifies AI workloads: chat, coding, summarization, long-context analysis, document QA,
creative writing. **MVP approach:** keyword/heuristic matching (e.g. "explain this error"
→ coding). This is intentionally simple — fast to ship, and easy to explain to judges.
ML-based classification is out of scope for MVP.

### FR-4 Optimization Engine
**Decision: rule-based, not ML, for the hackathon MVP.** A transparent decision table is
faster to build, easier to debug under time pressure, and — critically — easy to explain
live to judges ("battery dropped below 20%, so it switched here"). Historical-data-driven
or learned optimization policies are a stretch goal only, not part of the MVP engine.

Example rule table (expand as needed, kept in `backend/app/core/rules.py`):

| Condition | Action |
|---|---|
| Battery < 20% | Switch to Battery Saver profile |
| Available RAM < 2GB | Reduce context length; lower thread count |
| Workload = coding | Increase context window; prefer coding-tuned model |
| Workload = long-context | Prefer smaller quantization (e.g. INT4); larger context length |

Optimization targets: speed, quality, battery efficiency, balanced operation.

### FR-5 Dynamic Optimization
Adjusts configuration when system conditions change mid-session. Must be **tested live**,
not just implemented — e.g. unplug the charger or open a memory-heavy app during a session
and confirm ArmPilot reacts. This is scheduled explicitly in Sprint 2 (see SCHEDULE.md).

### FR-6 Optimization Log
All decisions recorded with timestamp, detected condition, action taken, and estimated
impact. Feeds the dashboard's decision history view. Stored in SQLite.

### FR-7 User Profiles
- **Speed Mode** — prioritizes tokens/sec, low latency
- **Quality Mode** — prioritizes model quality/accuracy
- **Battery Saver Mode** — prioritizes power efficiency, memory reduction
- **Automatic Mode** — ArmPilot makes all decisions

---

## Benchmarking Methodology

**Key change from v1:** report specific, reproducible measured numbers for the demo,
not wide ranges. Ranges are fine as directional targets (below) but the demo and the
final report should lead with one credible before/after result.

**Process:**
1. Define a fixed task set (e.g. one coding prompt, one summarization prompt, one
   long-context prompt) before Sprint 3.
2. For each task: run with optimization OFF and ON, 3–5 trials each, on the same device
   in the same power state.
3. Report the **median** of each metric, not best-case.
4. Pre-warm/pre-load all model variants involved before any benchmark or demo run — cold
   model loads will distort latency numbers and risk visibly stalling a live demo.

**Metrics collected:** tokens per second, time to first token, memory usage, CPU
utilization, battery consumption, swap usage.

**Directional targets** (used for planning, not asserted as guaranteed in the demo):
- Throughput improvement: 20–50%
- Time-to-first-token improvement: 20–40%
- Memory reduction: 20–50%
- Battery consumption reduction: 10–30%

---

## System Architecture

```
User Request
     ↓
Local AI Application
     ↓
ArmPilot Optimization Layer
  ├─ Hardware Detection (FR-1)
  ├─ System Monitoring (FR-2)
  ├─ Workload Classifier (FR-3)
  ├─ Optimization Engine / Rule Table (FR-4)
  └─ Optimization Log (FR-6)
     ↓
Ollama Runtime (pre-warmed models)
     ↓
Local Model
```

---

## MVP Scope

**Included:** Apple Silicon support, Ollama integration, hardware detection, benchmark
collection, rule-based optimization engine, dashboard, optimization logs.

**Excluded:** Distributed inference, cloud fallback, multi-device clustering,
reinforcement-learning optimization, Android support.

## Stretch Goals (in priority order given existing monitoring work)
1. **Thermal-aware optimization** — most demo-friendly stretch, since thermal monitoring
   is already built for FR-1/FR-2.
2. **Learning optimization policies** — use historical benchmark data to improve
   recommendations over time. Explicitly NOT part of MVP; mention only as future work.
3. **Cloud offloading** — route difficult tasks to cloud models.
4. **Distributed inference** — share inference workload across multiple Arm devices.

---

## Technology Stack

**Frontend:** React, TypeScript, TailwindCSS, Chart.js
**Backend:** FastAPI, Python
**Runtime Integration:** Ollama API
**Monitoring:** psutil + macOS system APIs (`pmset`, `powermetrics`)
**Storage:** SQLite

---

## Team Structure

Organized by vertical feature ownership rather than technical layer, so no single
person becomes a bottleneck and everyone can speak to optimization decisions, benchmark
methodology, architecture, and implementation in judge interviews.

| Member | Primary Ownership | Secondary Ownership |
|---|---|---|
| Member 1 | Hardware Detection + Benchmarking | Frontend |
| Member 2 | Optimization Engine | Backend APIs |
| Member 3 | Runtime Integration | Optimization Engine |
| Member 4 | Dashboard + Visualization | Benchmarking |

**Rotation policy:** Secondary ownership rotates weekly to spread knowledge. Primary
ownership of the two highest-risk features — **Optimization Engine** and **Runtime
Integration** — stays fixed through Week 1–2, since these are the pieces most likely to
have a costly mid-build handoff. Full rotation opens up in Sprint 3, once these pieces
are stable enough that handoff is cheap. See `docs/SCHEDULE.md` for the day-by-day plan.

---

## Demo Scenario

1. Launch local AI on an M3 MacBook Air; show baseline performance (ArmPilot disabled).
2. Enable ArmPilot.
3. Submit a long-context task.
4. ArmPilot detects workload complexity and recommends optimized settings.
5. Benchmark results show measured (not assumed) improvements.
6. User opens another heavy application.
7. ArmPilot adapts automatically (FR-5, tested live in Sprint 2).
8. Dashboard displays optimization decisions and resulting gains.

**Fallback plan:** if live model switching misbehaves during the demo, cut to a
pre-recorded clip or screenshots (`demo/fallback_assets/`). Do not rely solely on a live
cold-load switch under demo conditions.

---

## Risk Register

| Risk | Why it matters | Mitigation |
|---|---|---|
| Battery/thermal access on macOS is non-trivial | FR-1/FR-2 depend on it; psutil alone is insufficient | Validate on real demo device Day 1–2 |
| Cold model-switch latency | Could visibly stall the live demo right when proving speed gains | Pre-warm/pre-load all demo model variants before any run |
| Benchmark numbers as ranges rather than real results | Ranges read as less credible to judges than one real number | Fixed task set, repeated trials, report medians |
| Optimization engine complexity | Rule table can sprawl under time pressure | Keep rules explicit and in one file (`rules.py`); resist ML for MVP |
| Single point of knowledge on a risky feature | Bus factor risk if one person is stuck/unavailable | Secondary ownership + Sprint 3 full rotation |
| FR-5 (dynamic re-optimization) implemented but never tested live | Could fail silently in the actual demo | Explicit live test scheduled in Sprint 2 |

---

## Why ArmPilot Should Win

ArmPilot directly addresses the biggest barrier preventing widespread adoption of local
AI: configuration complexity. The project combines mobile AI, systems engineering, Arm
optimization, developer experience improvements, and measurable benchmarking — with a
transparent, explainable rule-based engine (not a black box) that judges can interrogate
line by line, backed by real before/after numbers rather than assumed ranges.
