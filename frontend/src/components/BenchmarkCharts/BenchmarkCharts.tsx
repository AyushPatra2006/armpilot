import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { api, type BenchmarkSummary } from "../../services/api";

export function BenchmarkCharts() {
  const [summary, setSummary] = useState<BenchmarkSummary | null>(null);

  useEffect(() => {
    api.getBenchmark().then(setSummary);
  }, []);

  if (!summary) {
    return (
      <section className="rounded-lg border border-ap-border bg-ap-surface p-6 font-mono text-sm text-ap-dim">
        Running benchmark…
      </section>
    );
  }

  const { before, after, speed_improvement_pct, memory_reduction_pct } = summary;
  const speedData = [
    { label: before.quantization, tokensPerSec: before.tokens_per_sec },
    { label: after.quantization, tokensPerSec: after.tokens_per_sec },
  ];

  return (
    <section className="rounded-lg border border-ap-border bg-ap-surface p-6 font-display text-ap-text">
      <span className="block font-mono text-[11px] uppercase tracking-wider text-ap-accent">
        Performance improvement
      </span>

      <div className="mb-2 mt-2 flex items-baseline gap-2.5">
        <span className="font-mono text-4xl font-semibold text-ap-accent">
          +{speed_improvement_pct}%
        </span>
        <span className="text-sm text-ap-dim">faster inference</span>
      </div>

      <div className="my-4">
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={speedData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="#2a2f38" />
            <XAxis dataKey="label" stroke="#8b929e" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#8b929e" fontSize={12} tickLine={false} axisLine={false} width={36} />
            <Tooltip
              contentStyle={{
                background: "#1b1f26",
                border: "1px solid #2a2f38",
                borderRadius: 6,
                fontFamily: "IBM Plex Mono, monospace",
                fontSize: 12,
              }}
              formatter={(value: number) => [`${value} tok/s`, "Speed"]}
            />
            <Bar dataKey="tokensPerSec" radius={[4, 4, 0, 0]} fill="#5eead4" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-5 border-t border-ap-border pt-4">
        <div>
          <span className="font-mono text-[11px] uppercase text-ap-dim">Before</span>
          <p className="mb-2 mt-1 text-[13px] text-ap-dim">{before.model}</p>
          <p className="font-mono text-xl">{before.tokens_per_sec} tok/s</p>
          <p className="mt-0.5 font-mono text-xs text-ap-dim">{before.memory_mb} MB</p>
        </div>
        <div>
          <span className="font-mono text-[11px] uppercase text-ap-accent">After</span>
          <p className="mb-2 mt-1 text-[13px] text-ap-dim">{after.model}</p>
          <p className="font-mono text-xl">{after.tokens_per_sec} tok/s</p>
          <p className="mt-0.5 font-mono text-xs text-ap-dim">{after.memory_mb} MB</p>
        </div>
      </div>

      {memory_reduction_pct !== null && (
        <p className="mt-3.5 text-xs text-ap-dim">
          Memory usage reduced by {memory_reduction_pct}%
        </p>
      )}
    </section>
  );
}
