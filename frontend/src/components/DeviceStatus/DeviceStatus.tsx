import { useEffect, useState } from "react";
import { api, type HardwareInfo } from "../../services/api";

export function DeviceStatus() {
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);

  useEffect(() => {
    api.getHardware().then(setHardware);
  }, []);

  if (!hardware) {
    return (
      <section className="rounded-lg border border-ap-border bg-ap-surface p-5 font-mono text-sm text-ap-dim">
        Detecting device…
      </section>
    );
  }

  const batteryLow = hardware.battery_percent < 20 && !hardware.plugged_in;

  return (
    <section className="rounded-lg border border-ap-border bg-ap-surface p-6 font-display text-ap-text">
      <span className="block font-mono text-[11px] uppercase tracking-wider text-ap-accent">
        Device detected
      </span>
      <h2 className="mb-4 mt-1 text-xl font-semibold">{hardware.device}</h2>

      <dl className="grid grid-cols-2 gap-5 sm:grid-cols-4">
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-ap-dim">Processor</dt>
          <dd className="mt-1 font-mono text-lg">{hardware.processor}</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-ap-dim">Cores</dt>
          <dd className="mt-1 font-mono text-lg">{hardware.cores}</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-ap-dim">Memory</dt>
          <dd className="mt-1 font-mono text-lg">{hardware.memory_gb}GB</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-ap-dim">Battery</dt>
          <dd className={`mt-1 font-mono text-lg ${batteryLow ? "text-ap-warn" : ""}`}>
            {hardware.battery_percent}%{" "}
            <span className="font-display text-[11px] text-ap-dim">
              {hardware.plugged_in ? "Plugged in" : "On battery"}
            </span>
          </dd>
        </div>
      </dl>
    </section>
  );
}
