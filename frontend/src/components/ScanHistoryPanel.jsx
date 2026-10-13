import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { fetchScanHistory } from "../api/client";
import ScanHistoryCard from "./ScanHistoryCard";

export default function ScanHistoryPanel() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchScanHistory({ limit: 50 })
      .then((data) => setRuns(data.runs))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section className="attack-path-panel results-empty">
        <p>Loading scan history…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="attack-path-panel results-error">
        <h2>Failed to load scan history</h2>
        <pre>{error}</pre>
      </section>
    );
  }

  const sorted = [...runs].sort((a, b) => new Date(b.started_at) - new Date(a.started_at));

  if (sorted.length === 0) {
    return (
      <section className="attack-path-panel results-empty">
        <p>No past scans yet.</p>
      </section>
    );
  }

  return (
    <div className="history-grid">
      {sorted.map((run) => (
        <ScanHistoryCard key={run.run_id} run={run} onSelect={(r) => navigate(`/history/${r.run_id}`)} />
      ))}
    </div>
  );
}
