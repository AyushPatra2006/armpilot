"""
Explicit rule table for the optimization engine. Kept separate from optimization_engine.py
so the decision logic is easy to read, demo, and explain live to judges.

How resolution works (plain English, for the judges Q&A):
  1. If the user has manually picked a mode ("speed" / "quality" / "battery_saver"),
     we skip the rule table entirely and just return that named baseline. Manual
     means manual - we don't second-guess the user's explicit choice.
  2. Otherwise ("automatic" mode), we check every rule's condition against the
     current device state. Every rule that matches gets collected.
  3. Each rule carries a `priority` (lower number = more urgent/important). We sort
     matched rules by priority and apply them in that order, filling in only the
     output fields (model/quant/threads/context_length/profile) that are still
     unset (None). Because the most urgent rules apply first and claim their
     fields first, a low-priority-number rule's value can never be clobbered by a
     less urgent one later - it already "locked in" that field.
     Concretely this means: thermal safety (priority 1) beats low-battery handling
     (priority 1, same tier) beats memory/swap pressure (priority 2) beats thermal
     "warm" throttling (priority 2) beats workload preferences like coding/long
     context (priority 3) beats "charging cancels battery saver" (priority 4, a
     documented no-op - see rule 8 below).
  4. Any output field no rule ever set falls back to the "speed" baseline's value
     (a safe, fast default), and the "profile" label falls back to "automatic" to
     make it clear this configuration was assembled from rules rather than being
     one of the three named presets - unless literally no rule matched at all, in
     which case we just return the "speed" baseline outright.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

# A field value can be a plain value, or a callable that computes the value from
# the current state dict. We need callables for anything that depends on the
# device's *current* thread count (e.g. "cut threads in half"), since that's not
# knowable ahead of time.
FieldValue = Union[Any, Callable[[Dict[str, Any]], Any]]


@dataclass
class Rule:
    """
    One row of the decision table.

    `condition` receives the current state dict and returns True/False.
    All output fields default to None, meaning "this rule doesn't care about this
    field" - it will never override a value another rule already set for it.
    `priority` is lower-wins: 1 is the most urgent (thermal/safety), higher numbers
    are progressively more like "nice to have" workload preferences.
    """

    condition: Callable[[Dict[str, Any]], bool]
    priority: int
    model: Optional[FieldValue] = None
    quant: Optional[FieldValue] = None
    threads: Optional[FieldValue] = None
    context_length: Optional[FieldValue] = None
    profile: Optional[FieldValue] = None


def _resolve(value: Optional[FieldValue], state: Dict[str, Any]) -> Any:
    """Evaluate a field value against the current state, if it's a callable."""
    if callable(value):
        return value(state)
    return value


# ---------------------------------------------------------------------------
# The rule table itself, written in the same order as the spec's "#" column.
# NOTE: list order here is just for readability/traceability back to the spec -
# resolve_rules() re-sorts by `priority` before applying anything, since that's
# what actually determines who wins.
# ---------------------------------------------------------------------------
RULES: List[Rule] = [
    # 1. Thermal emergency: halve threads immediately, regardless of anything else.
    Rule(
        condition=lambda s: s.get("thermal") == "hot",
        priority=1,
        threads=lambda s: s["current_threads"] // 2,
    ),
    # 2. Critically low battery, unplugged: go full battery saver.
    Rule(
        condition=lambda s: s.get("battery_pct", 100) < 20 and not s.get("charging", False),
        priority=1,
        model="llama3.2:3b",
        quant="Q4_K_M",
        threads=4,
        context_length=8192,
        profile="battery_saver",
    ),
    # 3. Critically low battery + a long-context workload is an even worse combo
    #    (long context = more compute/memory) - same battery_saver response.
    Rule(
        condition=lambda s: s.get("battery_pct", 100) < 20 and s.get("workload") == "long_context",
        priority=1,
        model="llama3.2:3b",
        quant="Q4_K_M",
        threads=4,
        context_length=8192,
        profile="battery_saver",
    ),
    # 4. Thermal warning (not yet critical): back off threads by 2, but not below 2.
    Rule(
        condition=lambda s: s.get("thermal") == "warm",
        priority=2,
        threads=lambda s: max(2, s["current_threads"] - 2),
    ),
    # 5. Low available RAM: shrink quantization/context/threads to keep things running.
    Rule(
        condition=lambda s: s.get("available_ram_gb", 999) < 2,
        priority=2,
        quant="Q4_K_M",
        threads=lambda s: max(2, s["current_threads"] // 2),
        context_length=8192,
    ),
    # 6. High swap usage is the same signal as low RAM (system is already paging) -
    #    respond the same way.
    Rule(
        condition=lambda s: bool(s.get("swap_usage_high")),
        priority=2,
        quant="Q4_K_M",
        threads=lambda s: max(2, s["current_threads"] // 2),
        context_length=8192,
    ),
    # 7. Low RAM specifically while coding: still prefer the coding-tuned model,
    #    just under the same memory-safe quant/threads/context constraints as rule 5.
    Rule(
        condition=lambda s: s.get("available_ram_gb", 999) < 2 and s.get("workload") == "coding",
        priority=2,
        model="qwen2.5-coder:7b",
        quant="Q4_K_M",
        threads=lambda s: max(2, s["current_threads"] // 2),
        context_length=8192,
    ),
    # 8. Low battery but plugged in: charging removes the urgency, so this rule
    #    intentionally sets nothing. It exists purely to document, explicitly, that
    #    "low battery + charging" is a recognized case that deliberately does NOT
    #    trigger battery_saver (unlike rules 2/3). Its low priority (4) means it
    #    would never win a field anyway - it's a no-op by design, kept for clarity
    #    when explaining the table to judges.
    Rule(
        condition=lambda s: s.get("battery_pct", 100) < 20 and s.get("charging", False),
        priority=4,
    ),
    # 9. Coding workload: prefer the coding-tuned model with a roomier context window.
    Rule(
        condition=lambda s: s.get("workload") == "coding",
        priority=3,
        model="qwen2.5-coder:7b",
        quant="Q4_K_M",
        context_length=16384,
    ),
    # 10. Long-context workload: prefer the larger-context model with a big window.
    Rule(
        condition=lambda s: s.get("workload") == "long_context",
        priority=3,
        model="qwen3:8b",
        quant="Q4_K_M",
        context_length=32768,
    ),
]


# ---------------------------------------------------------------------------
# Named baseline profiles. These are NOT condition-based - they're what we return
# outright when the user manually selects a mode instead of leaving things on
# "automatic". Threads scale off `max_cores`, so they're computed lazily.
# ---------------------------------------------------------------------------
BASELINE_PROFILES: Dict[str, Dict[str, Any]] = {
    "speed": {
        "model": "llama3.2:3b",
        "quant": "Q4_K_M",
        "threads": lambda max_cores: max_cores,
        "context_length": 8192,
        "profile": "speed",
    },
    "quality": {
        "model": "qwen3:8b",
        "quant": "Q4_K_M",
        # Moderate thread count - qwen3:8b is heavier, so we don't need (or want)
        # to throw every core at it the way "speed" does.
        "threads": lambda max_cores: max_cores // 2 + 1,
        "context_length": 32768,
        "profile": "quality",
        # qwen3:8b MUST always be invoked with thinking disabled - benchmarking
        # showed it's ~2x slower with thinking on, for negligible quality gain
        # in this use case. Non-negotiable, hence baked into the baseline itself.
        "extra_flag": "--think=false",
    },
    "battery_saver": {
        "model": "llama3.2:3b",
        "quant": "Q4_K_M",
        "threads": lambda max_cores: max(2, max_cores // 2),
        "context_length": 8192,
        "profile": "battery_saver",
    },
}


def get_baseline_profile(name: str, max_cores: int) -> Dict[str, Any]:
    """Resolve a named baseline profile's thread count against the real core count."""
    if name not in BASELINE_PROFILES:
        raise ValueError(
            f"Unknown profile '{name}'. Expected one of {list(BASELINE_PROFILES)} or 'automatic'."
        )
    template = BASELINE_PROFILES[name]
    resolved = {key: (value(max_cores) if callable(value) else value) for key, value in template.items()}
    resolved.setdefault("extra_flag", None)
    return resolved


def resolve_rules(state: Dict[str, Any], max_cores: int) -> Dict[str, Any]:
    """
    Resolve the current device/workload state into a concrete inference config.

    Args:
        state: current readings. Expected keys (all optional - missing keys are
            treated as "no signal" and simply won't trigger their rules):
              - mode: "automatic" (default), "speed", "quality", or "battery_saver"
              - battery_pct: float/int, 0-100
              - charging: bool
              - available_ram_gb: float
              - thermal: "nominal" | "warm" | "hot"
              - swap_usage_high: bool
              - workload: "chat" | "coding" | "long_context" | ...
              - current_threads: int, the thread count currently in use (defaults
                to max_cores if not supplied, so relative rules like "halve it"
                have something sane to work from)
        max_cores: number of CPU cores available on this device.

    Returns:
        {"model": str, "quant": str, "threads": int, "context_length": int,
         "profile": str, "extra_flag": Optional[str]}
    """
    mode = state.get("mode", "automatic")

    # Manual override: the user picked a lane, we drive in that lane. No rules.
    if mode and mode != "automatic":
        return get_baseline_profile(mode, max_cores)

    # Work off a copy so we can safely default current_threads without mutating
    # the caller's state dict.
    working_state = dict(state)
    working_state.setdefault("current_threads", max_cores)

    matched_rules = [rule for rule in RULES if rule.condition(working_state)]
    # Lower priority number = more urgent = applied (and therefore "locked in") first.
    matched_rules.sort(key=lambda rule: rule.priority)

    result: Dict[str, Any] = {
        "model": None,
        "quant": None,
        "threads": None,
        "context_length": None,
        "profile": None,
    }
    for rule in matched_rules:
        for field in result:
            if result[field] is not None:
                # A more urgent rule already claimed this field - it wins, period.
                continue
            value = _resolve(getattr(rule, field), working_state)
            if value is not None:
                result[field] = value

    # Automatic mode, but nothing in the table matched at all (e.g. everything is
    # nominal and the workload is plain "chat") - just use the fast, safe default.
    if not matched_rules:
        return get_baseline_profile("speed", max_cores)

    # Some rules matched but left a few fields untouched (e.g. a workload rule
    # sets model/quant/context but never touches threads). Fill remaining gaps
    # from the "speed" baseline as a sensible, safe default.
    fallback = get_baseline_profile("speed", max_cores)
    for field in ("model", "quant", "threads", "context_length"):
        if result[field] is None:
            result[field] = fallback[field]

    # Only label the result with a named profile if a rule explicitly set one
    # (e.g. battery_saver). Otherwise this is a bespoke mix of rules, so we call
    # it "automatic" rather than mislabeling it as one of the three presets.
    if result["profile"] is None:
        result["profile"] = "automatic"

    result.setdefault("extra_flag", None)
    return result


if __name__ == "__main__":
    examples = [
        {
            "battery_pct": 15,
            "charging": False,
            "available_ram_gb": 8,
            "thermal": "nominal",
            "swap_usage_high": False,
            "workload": "chat",
            "current_threads": 8,
        },
        {
            "battery_pct": 80,
            "charging": True,
            "available_ram_gb": 16,
            "thermal": "hot",
            "swap_usage_high": False,
            "workload": "coding",
            "current_threads": 8,
        },
        {
            "battery_pct": 60,
            "charging": True,
            "available_ram_gb": 1.2,
            "thermal": "warm",
            "swap_usage_high": True,
            "workload": "long_context",
            "current_threads": 8,
        },
    ]

    for i, state in enumerate(examples, start=1):
        print(f"Example {i}: {state}")
        print("  ->", resolve_rules(state, max_cores=8))
        print()

    # Example 1: low battery + unplugged -> rule 2 fires -> textbook battery_saver.
    # Example 2: thermal "hot" (priority 1) claims threads before the "coding"
    #            workload rule (priority 3) can, but coding still wins model/quant/
    #            context since thermal never touches those fields.
    # Example 3: shows priority actually resolving a conflict: "warm" thermal sets
    #            threads=6, low RAM + high swap (priority 2) then locks quant/context
    #            down to 8192 for safety - beating out the long_context workload
    #            rule (priority 3) that would have preferred a 32768 context window.

    print("Manual 'quality' mode (ignores all rules, includes the qwen3 no-think flag):")
    print("  ->", resolve_rules({"mode": "quality"}, max_cores=8))
