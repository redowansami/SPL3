import { Fragment, useState } from "react";

import { fetchMitigation } from "../api/client";
import MitigationModal from "./MitigationModal";

function truncate(text, max = 400) {
  if (!text || text.length <= max) return text;
  return text.slice(0, max) + "…";
}

export default function AttackPathPanel({ isRunning, error, result, elapsed = 0 }) {
  const [mitigation, setMitigation] = useState(null);

  async function openMitigation(probe) {
    setMitigation({ probe, loading: true, error: null, data: null });
    try {
      const data = await fetchMitigation(probe);
      setMitigation({ probe, loading: false, error: null, data });
    } catch (err) {
      setMitigation({ probe, loading: false, error: err.message, data: null });
    }
  }

  function closeMitigation() {
    setMitigation(null);
  }

  if (isRunning) {
    return (
      <section className="attack-path-panel results-empty">
        <p>Running probe against target... {Math.round(elapsed)}s elapsed.</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="attack-path-panel results-error">
        <h2>Scan failed</h2>
        <pre>{error}</pre>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="attack-path-panel results-empty">
        <p>Select a probe on the left and click RUN to scan the target.</p>
      </section>
    );
  }

  if (result.status === "cancelled") {
    return (
      <section className="attack-path-panel results-error">
        <h2>Scan cancelled</h2>
        <pre>{result.error}</pre>
      </section>
    );
  }

  if (result.status === "timed_out") {
    return (
      <section className="attack-path-panel results-error">
        <h2>Scan timed out</h2>
        <pre>{result.error}</pre>
      </section>
    );
  }

  if (!result.ok) {
    return (
      <section className="attack-path-panel results-error">
        <h2>Garak run failed</h2>
        <pre>{result.error}</pre>
      </section>
    );
  }

  return (
    <section className="attack-path-panel">
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

      {result.attack_paths.length === 0 ? (
        <p className="no-failures">No successful attack paths for this probe.</p>
      ) : (
        <div className="attack-path-list">
          {result.attack_paths.map((item, idx) => (
            <div key={`${item.attempt_seq}-${idx}`} className="attack-path-flow">
              <div className="attack-path-heading">Attempt #{item.attempt_seq}</div>

              <div className="attack-path-node attack-path-goal">
                <span className="attack-path-node-label">Goal / Technique</span>
                <div className="attack-path-node-body">{item.goal}</div>
                <div className="attack-path-node-sub">{item.probe}</div>
              </div>
              <div className="attack-path-arrow" />

              {item.prompt_turns.map((turn, ti) => (
                <Fragment key={ti}>
                  <div className="attack-path-node attack-path-prompt">
                    <span className="attack-path-node-label">
                      {item.prompt_turns.length > 1 ? `Injected Prompt (turn ${ti + 1})` : "Injected Prompt"}
                    </span>
                    <pre className="attack-path-node-body">{truncate(turn)}</pre>
                  </div>
                  <div className="attack-path-arrow" />
                </Fragment>
              ))}

              <div className="attack-path-node attack-path-output">
                <span className="attack-path-node-label">Target Output</span>
                <pre className="attack-path-node-body">{truncate(item.output)}</pre>
              </div>
              <div className="attack-path-arrow" />

              <div className="attack-path-node attack-path-exploit">
                <span className="attack-path-node-label">Exploit Confirmed</span>
                <div className="attack-path-node-sub">
                  {item.triggers.length > 0 ? (
                    item.triggers.map((t, ti) => (
                      <span key={ti} className="attack-path-trigger-badge">
                        {t}
                      </span>
                    ))
                  ) : (
                    <span className="attack-path-trigger-badge attack-path-trigger-badge-empty">
                      detector: {item.detector}
                    </span>
                  )}
                </div>
                <div className="attack-path-node-score">score: {item.score.toFixed(2)}</div>
                <button className="mitigation-button" onClick={() => openMitigation(item.probe)}>
                  Mitigation
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {mitigation && (
        <MitigationModal
          title={mitigation.probe}
          loading={mitigation.loading}
          error={mitigation.error}
          data={mitigation.data}
          onClose={closeMitigation}
        />
      )}
    </section>
  );
}
