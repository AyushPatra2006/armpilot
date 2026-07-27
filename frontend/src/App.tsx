import { Dashboard } from "./components/Dashboard/Dashboard";

/**
 * Primary UI is the dashboard (device → recommendation → improvement).
 * Runtime optimize/run APIs remain available via services/api.ts for
 * demos, scripts, and future controls wired into the same Dashboard.
 */
function App() {
  return <Dashboard />;
}

export default App;
