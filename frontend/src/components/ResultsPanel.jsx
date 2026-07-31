export default function ResultsPanel({ isRunning, error, result, elapsed = 0 }) {
  if (isRunning) {
    return (
      <section className="results-panel results-empty">
        <p>Running probe against target... {Math.round(elapsed)}s elapsed.</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="results-panel results-error">
        <h2>Scan failed</h2>
        <pre>{error}</pre>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="results-panel results-empty">
        <p>Select a probe on the left and click RUN to scan the target.</p>
      </section>
    );
  }

  if (result.status === "cancelled") {
    return (
      <section className="results-panel results-error">
        <h2>Scan cancelled</h2>
        <pre>{result.error}</pre>
      </section>
    );
  }

  if (result.status === "timed_out") {
    return (
      <section className="results-panel results-error">
        <h2>Scan timed out</h2>
        <pre>{result.error}</pre>
      </section>
    );
  }

  if (!result.ok) {
    return (
      <section className="results-panel results-error">
        <h2>Garak run failed</h2>
        <pre>{result.error}</pre>
      </section>
    );
  }

  return (
    <section className="results-panel">
      <div className="results-summary">
        <h2>Results — {result.garak_probe}</h2>
        <div className="results-stats">
          <div className="stat">
            <span className="stat-value">{result.attempts_evaluated}</span>
            <span className="stat-label">Attempts evaluated</span>
          </div>
          <div className={`stat ${result.failure_count > 0 ? "stat-bad" : "stat-good"}`}>
            <span className="stat-value">{result.failure_count}</span>
            <span className="stat-label">Failures found</span>
          </div>
        </div>
      </div>

      {result.failure_count === 0 ? (
        <p className="no-failures">No failures detected for this probe.</p>
      ) : (
        <ul className="failure-list">
          {result.failures.map((failure, idx) => (
            <li key={idx} className="failure-item">
              <div className="failure-header">
                <span className="failure-detector">{failure.detector}</span>
                <span className="failure-score">score: {failure.score.toFixed(2)}</span>
              </div>
              <div className="failure-block">
                <span className="failure-block-label">Prompt</span>
                <pre>{failure.prompt}</pre>
              </div>
              <div className="failure-block">
                <span className="failure-block-label">Output</span>
                <pre>{failure.output}</pre>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
