import { DeviceStatus } from "../DeviceStatus/DeviceStatus";
import { OptimizationLog } from "../OptimizationLog/OptimizationLog";
import { BenchmarkCharts } from "../BenchmarkCharts/BenchmarkCharts";

/**
 * Renders the full ArmPilot story in one screen:
 *   Device Detected -> Optimization Recommendation -> Applied Config -> Performance Improvement
 *
 * Each section fetches its own data independently, so one slow or
 * failing endpoint never blocks the rest of the dashboard — important
 * for a live demo where any one backend piece might still be mid-build.
 */
export function Dashboard() {
  return (
    <div className="min-h-screen bg-ap-bg p-8 font-display">
      <header className="mb-6 flex items-baseline gap-3.5">
        <span className="font-mono text-lg font-bold tracking-tight text-ap-text">
          ArmPilot
        </span>
        <span className="text-[13px] text-ap-dim">
          The intelligent runtime manager for local AI on Arm devices.
        </span>
      </header>

      <div className="grid max-w-5xl grid-cols-1 gap-5 sm:grid-cols-2">
        <DeviceStatus />
        <OptimizationLog />
        <div className="sm:col-span-2">
          <BenchmarkCharts />
        </div>
      </div>
    </div>
  );
}















