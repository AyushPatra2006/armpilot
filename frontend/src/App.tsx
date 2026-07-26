import React, { useEffect, useState } from "react";
import { api, HardwareInfo, OptimizeDecisionResponse } from "./services/api";

function App() {
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [optimizeResult, setOptimizeResult] = useState<OptimizeDecisionResponse | null>(null);
  const [runOutput, setRunOutput] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.device().then(setHardware).catch((err) => setError(String(err)));
  }, []);

  const handleOptimize = async () => {
    try {
      setError(null);
      const result = await api.optimize("Summarize a 250-page research paper", "automatic");
      setOptimizeResult(result);
    } catch (err) {
      setError(String(err));
    }
  };

  const handleRun = async () => {
    try {
      setError(null);
      const result = await api.run("qwen3:8b", "Explain AI optimization on Arm.", {
        num_ctx: 16000,
        num_thread: 8,
      });
      setRunOutput(result);
    } catch (err) {
      setError(String(err));
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold">ArmPilot</h1>
            <p className="text-slate-400">Intelligent runtime optimization for local AI on Arm.</p>
          </div>
          <div className="flex gap-3">
            <button className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-950" onClick={handleOptimize}>
              Optimize
            </button>
            <button className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium" onClick={handleRun}>
              Run Ollama
            </button>
          </div>
        </div>

        {error ? <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-red-200">{error}</div> : null}

        <div className="grid gap-4 md:grid-cols-2">
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-3 text-lg font-medium">Hardware</h2>
            <pre className="overflow-auto text-xs text-slate-300">{JSON.stringify(hardware, null, 2)}</pre>
          </section>
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-3 text-lg font-medium">Optimization</h2>
            <pre className="overflow-auto text-xs text-slate-300">{JSON.stringify(optimizeResult, null, 2)}</pre>
          </section>
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-4 md:col-span-2">
            <h2 className="mb-3 text-lg font-medium">Runtime Output</h2>
            <pre className="overflow-auto text-xs text-slate-300">{JSON.stringify(runOutput, null, 2)}</pre>
          </section>
        </div>
      </div>
    </div>
  );
}

export default App;
