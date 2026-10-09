export default function ScanHistoryCard({ run, onSelect }) {
  const isGarak = run.engine === "garak";
  const passed =
    isGarak && run.attempts_evaluated != null && run.failure_count != null
      ? run.attempts_evaluated - run.failure_count
      : null;

  return (
    <button type="button" className="history-card" onClick={() => onSelect(run)}>
      <div className="history-card-url" title={run.target_url}>
        {run.target_url}
      </div>
      <div className="history-card-meta">
        <span className="history-card-engine">
          {isGarak ? "Garak" : run.engine === "custom" ? "Custom" : "PyRIT"}
        </span>
        <span className="history-card-status">{run.status}</span>
        <span className="history-card-time">{new Date(run.started_at).toLocaleString()}</span>
      </div>

      <div className="results-stats">
        {isGarak ? (
          <>
            <div className="stat">
              <span className="stat-value">{run.attempts_evaluated ?? "—"}</span>
              <span className="stat-label">Attempts</span>
            </div>
            <div className="stat stat-good">
              <span className="stat-value">{passed ?? "—"}</span>
              <span className="stat-label">Passed</span>
            </div>
            <div className={`stat ${run.failure_count > 0 ? "stat-bad" : "stat-good"}`}>
              <span className="stat-value">{run.failure_count ?? "—"}</span>
              <span className="stat-label">Failed</span>
            </div>
          </>
        ) : (
          <>
            <div className="stat">
              <span className="stat-value">{run.executed_turns ?? "—"}</span>
              <span className="stat-label">Turns</span>
            </div>
            <div className={`stat ${run.achieved ? "stat-bad" : "stat-good"}`}>
              <span className="stat-value">{run.achieved ? "Yes" : "No"}</span>
              <span className="stat-label">Achieved</span>
            </div>
          </>
        )}
      </div>
    </button>
  );
}
