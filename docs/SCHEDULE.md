# ArmPilot — 3-Week Build Schedule

This is a living document. Update the "Status" column as you go. If you're picking this
up mid-project, read this file plus `docs/PRD.md` before writing any code — they're kept
in sync as the source of truth.

**Team:**
- Member 1 — Primary: Hardware Detection + Benchmarking · Secondary: Frontend
- Member 2 — Primary: Optimization Engine · Secondary: Backend APIs
- Member 3 — Primary: Runtime Integration · Secondary: Optimization Engine
- Member 4 — Primary: Dashboard + Visualization · Secondary: Benchmarking

**Rotation policy:** Secondary ownership rotates weekly (see Week 2). Primary ownership
of the two highest-risk features — **Optimization Engine** and **Runtime Integration** —
stays fixed through Week 1–2 and only opens up for full rotation in Week 3, once those
pieces are stable enough that a handoff is cheap.

**Decision owners for Sprint 3:** name one person as final call on benchmark methodology
and one as final call on the demo script, even during the all-hands phase, so ties get
broken quickly. (Assign these names once you hit Sprint 3 — don't decide too early.)

---

## Sprint 1 — Foundation (Days 1–4)
Everyone works together. Goal: by end of Day 4, everyone understands the models, the
runtime, the benchmark process, and the architecture. No feature ownership yet.

### Day 1
- [ ] All: read PRD.md together, confirm scope, confirm demo device(s) available
- [ ] Member 1: start device detection (model, cores, RAM) — psutil basics
- [ ] Member 1 or 4: **validate battery/thermal monitoring path on the actual demo Mac now**
      (`pmset -g batt`, test `powermetrics` permission requirements). This is a known risk
      item — do not defer it.
- [ ] Member 3: install Ollama, pull 2–3 model/quant variants, do a first cold-load timing test
- [ ] Member 2: sketch the rule table (see PRD FR-4) on paper/whiteboard, no code yet

### Day 2
- [ ] Member 1: finish device detection v1 (RAM, CPU cores, GPU cores, Neural Engine flag)
- [ ] Member 1/4: confirm battery/thermal monitoring works reliably; document the exact
      command/permissions needed in `backend/app/core/hardware_detection.py` docstring
- [ ] Member 3: measure and record cold-load vs warm-switch time for each model variant —
      this number determines whether pre-warming is mandatory (it almost certainly is)
- [ ] Member 2: implement rule table skeleton in `rules.py` with fake/hardcoded inputs
- [ ] Member 4: scaffold frontend project, confirm it builds and talks to a dummy backend route

### Day 3
- [ ] Member 1: system monitoring loop (5s polling: CPU, memory, swap, battery, thermal)
- [ ] Member 3: build `ollama_client.py` — pull, load, switch, generate against real Ollama
- [ ] Member 2: workload classifier v1 (keyword heuristics — chat/coding/summarization/etc.)
- [ ] Member 4: SQLite schema draft for OptimizationEvent / BenchmarkRun / DeviceSnapshot

### Day 4
- [ ] All: baseline benchmark run — one task, optimization OFF, record real numbers
- [ ] All: sync — does everyone understand the full pipeline end to end? If not, fix that
      before Sprint 2 starts.
- [ ] Checkpoint: hardware detection, Ollama integration, and rule table skeleton all work
      in isolation (ugly output is fine).

---

## Sprint 2 — Core Features (Days 5–10)
Split by feature. Primary owner drives; secondary owner is expected to be able to pick
up the work if primary is blocked.

### Feature A: Hardware Detection — Member 1 (+ Member 4)
- Day 5–6: RAM/CPU/battery monitoring hardened, tested on more than one Mac if available
- Day 7: thermal state integration; confirm behavior under real thermal throttling if possible

### Feature B: Optimization Engine — Member 2 (+ Member 3)
- Day 5–6: full rule table wired to real sensor inputs (not fake data anymore)
- Day 7–8: profile selection (Speed / Quality / Battery Saver / Automatic) implemented
- Day 8: dynamic re-optimization (FR-5) — test condition changes mid-session (unplug
  charger, open a memory-heavy app) and confirm the engine reacts

### Feature C: Runtime Integration — Member 3 (+ Member 1)
- Day 5–6: model switching wired to optimization engine output
- Day 7: **pre-warming strategy implemented** — pre-pull/pre-load all demo model variants
  so live switching doesn't show cold-load latency
- Day 8: Member 4 joins briefly to help stress-test this feature given it's the highest
  demo-failure risk

### Feature D: Dashboard — Member 4 (+ Member 2)
- Day 5–6: dashboard shell + DeviceStatus widget wired to real backend data
- Day 7–8: OptimizationLog view wired to SQLite log
- Day 9–10: BenchmarkCharts wired to real benchmark data

### Days 9–10 (integration)
- [ ] Full pipeline end-to-end: sensors → classifier → optimization engine → Ollama → log → dashboard
- [ ] Optimization log accumulating real (not synthetic) decisions
- [ ] Checkpoint: could you demo this today, even roughly? If not, identify the blocker now.

---

## Sprint 3 — Benchmarking, Polish, Demo Prep (Days 11–17, or through Day 21 if using full 3 weeks)
All hands. Named decision-owners (benchmark methodology, demo script) break ties.

- Day 11–13: Structured benchmark runs — fixed task set, multiple trials, report **medians**,
  not ranges. This is what goes on the dashboard and in the PRD's success metrics section.
- Day 13–14: Full rotation opens up — everyone should touch every part of the codebase at
  least once now, since handoffs are cheap at this stage
- Day 15: Stretch goal — thermal-aware optimization (only if core is fully stable)
- Day 15–16: Dashboard polish — this is what judges look at most
- Day 16: Demo script finalized, fallback assets (recorded clip / screenshots) prepared
- Day 17+: Full demo rehearsals — minimum 3 full run-throughs on the actual presentation
  setup. Everyone should be able to answer "what did you personally work on?" with specifics.

---

## Standing Risk Watchlist
Revisit these every few days — if any of these slip, it affects the demo directly.

| Risk | Mitigation | Status |
|---|---|---|
| Battery/thermal access on macOS is fiddly | Validated Day 1–2, documented in code | |
| Cold model-switch latency kills live demo | Pre-warm all demo models before any run | |
| Benchmark claims are ranges, not real numbers | Fixed task set, repeated trials, report medians | |
| One person becomes sole owner of a risky piece | Secondary ownership + Sprint 3 full rotation | |
| Dynamic re-optimization (FR-5) never actually tested live | Explicit test in Sprint 2 Day 8 | |
