// Shared types live here too, to keep this a single import for
// every component. Split into types.ts if this grows.

export interface HardwareInfo {
  device: string;
  processor: string;
  cores: number;
  memory_gb: number;
  battery_percent: number;
  plugged_in: boolean;
}

export interface OptimizationLogEntry {
  timestamp: string;
  model: string;
  change: string;
  reason: string;
  expected_impact: string;
}

export interface BenchmarkRecord {
  model: string;
  quantization: string;
  tokens_per_sec: number;
  memory_mb: number;
  time_to_first_token_ms: number;
}

export interface BenchmarkSummary {
  before: BenchmarkRecord;
  after: BenchmarkRecord;
  speed_improvement_pct: number;
  memory_reduction_pct: number | null;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Demo-safe fallbacks so the dashboard never shows a blank screen if
// the backend isn't running (e.g. walking between demo booths).
const FALLBACK_HARDWARE: HardwareInfo = {
  device: "MacBook Air M3",
  processor: "Apple M3",
  cores: 8,
  memory_gb: 16,
  battery_percent: 35,
  plugged_in: false,
};

const FALLBACK_LOGS: OptimizationLogEntry[] = [
  {
    timestamp: "10:32 AM",
    model: "Qwen3 8B",
    change: "INT8 → INT4",
    reason: "Reduce memory usage",
    expected_impact: "Lower latency, -35% power",
  },
];

const FALLBACK_BENCHMARK: BenchmarkSummary = {
  before: { model: "Qwen3 8B INT8", quantization: "INT8", tokens_per_sec: 30, memory_mb: 8000, time_to_first_token_ms: 360 },
  after: { model: "Qwen3 8B INT4", quantization: "INT4", tokens_per_sec: 45, memory_mb: 4300, time_to_first_token_ms: 205 },
  speed_improvement_pct: 50,
  memory_reduction_pct: 46.25,
};

async function safeGet<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${BASE_URL}${path}`);
    if (!res.ok) throw new Error(`${path} returned ${res.status}`);
    return (await res.json()) as T;
  } catch (err) {
    console.warn(`[api] falling back to demo data for ${path}:`, err);
    return fallback;
  }
}

export const api = {
  getHardware: () => safeGet<HardwareInfo>("/api/hardware", FALLBACK_HARDWARE),
  getLogs: () => safeGet<OptimizationLogEntry[]>("/api/logs", FALLBACK_LOGS),
  getBenchmark: () => safeGet<BenchmarkSummary>("/api/benchmark", FALLBACK_BENCHMARK),
};
