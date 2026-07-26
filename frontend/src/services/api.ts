export type HardwareInfo = {
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

export type OptimizeDecisionResponse = {
  hardware: HardwareInfo;
  workload: { label: string; confidence: number; reason: string };
  decision: Record<string, unknown>;
};

const API_BASE = import.meta.env?.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
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
  health: () => request<{ status: string }>("/health"),
  device: () => request<HardwareInfo>("/device"),
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
