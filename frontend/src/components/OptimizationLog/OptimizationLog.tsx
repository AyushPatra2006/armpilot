import { useEffect, useState } from "react";
import { api, type OptimizationLogEntry } from "../../services/api";

export function OptimizationLog() {
  const [logs, setLogs] = useState<OptimizationLogEntry[] | null>(null);

  useEffect(() => {
    api.getLogs().then(setLogs);
  }, []);

  return (
    <section className="rounded-lg border border-ap-border bg-ap-surface p-6 font-display text-ap-text">
      <span className="block font-mono text-[11px] uppercase tracking-wider text-ap-accent">
        Optimization applied
      </span>

      {!logs && <p className="mt-4 text-sm text-ap-dim">Waiting for optimization decisions…</p>}
      {logs?.length === 0 && (
        <p className="mt-4 text-sm text-ap-dim">No optimizations yet. ArmPilot is monitoring.</p>
      )}

      <ol className="mt-4 list-none">
        {logs?.map((entry, i) => (
          <li
            key={`${entry.timestamp}-${i}`}
            className="flex gap-4 border-t border-ap-border py-3 first:border-t-0 first:pt-0"
          >
            <span className="min-w-[68px] pt-0.5 font-mono text-xs text-ap-dim">
              {entry.timestamp}
            </span>
            <div className="flex-1">
              <div className="flex items-baseline gap-2.5 text-sm">
                <strong>{entry.model}</strong>
                <span className="font-mono text-[13px] text-ap-accent">{entry.change}</span>
              </div>
              <p className="mt-1 text-[13px] text-ap-dim">{entry.reason}</p>
              <p className="mt-0.5 font-mono text-xs text-ap-accent">{entry.expected_impact}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
