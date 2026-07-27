// Shared API client + types for dashboard components and runtime controls.

export interface HardwareInfo {
  device: string;
  processor: string;
  cores: number;
  memory_gb: number;
  battery_percent: number;
  plugged_in: boolean;
}

/** Full hardware payload from GET /api/device (runtime integration). */
export type DeviceHardwareInfo = {
  device_model: string;
  architecture: string;
  cpu_cores: number;
  logical_cores: number;
  total_ram_gb: number;
  available_ram_gb: number;
  swap_usage_gb: number;
  battery_pct: number | null;
  charging: boolean | null;
  thermal_state: string;
};

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

export type OptimizeDecisionResponse = {
  hardware: DeviceHardwareInfo;
  workload: { label: string; confidence: number; reason: string };
  decision: Record<string, unknown>;
};

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
  before: {
    model: "Qwen3 8B INT8",
    quantization: "INT8",
    tokens_per_sec: 30,
    memory_mb: 8000,
    time_to_first_token_ms: 360,
  },
  after: {
    model: "Qwen3 8B INT4",
    quantization: "INT4",
    tokens_per_sec: 45,
    memory_mb: 4300,
    time_to_first_token_ms: 205,
  },
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}/api${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  // Dashboard (GET, with demo fallbacks)
  getHardware: () => safeGet<HardwareInfo>("/api/hardware", FALLBACK_HARDWARE),
  getLogs: () => safeGet<OptimizationLogEntry[]>("/api/logs", FALLBACK_LOGS),
  getBenchmark: () => safeGet<BenchmarkSummary>("/api/benchmark", FALLBACK_BENCHMARK),

  // Runtime integration
  health: () => request<{ status: string }>("/health"),
  device: () => request<DeviceHardwareInfo>("/device"),
  optimize: (prompt: string, mode = "automatic") =>
    request<OptimizeDecisionResponse>("/optimize", {
      method: "POST",
      body: JSON.stringify({ prompt, mode }),
    }),
  run: (model: string, prompt: string, settings: Record<string, unknown> = {}) =>
    request<{
      response: string;
      tokens_generated: number;
      latency: number;
      tokens_per_second: number;
      time_to_first_token: number;
      model: string;
    }>("/run", {
      method: "POST",
      body: JSON.stringify({ model, prompt, settings }),
    }),
  benchmark: (model: string, prompt: string, settings: Record<string, unknown> = {}) =>
    request("/benchmark", {
      method: "POST",
      body: JSON.stringify({ model, prompt, settings }),
    }),
  log: () => request<{ items: Array<Record<string, unknown>> }>("/log"),
};
