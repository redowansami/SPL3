import { useState } from "react";

import { fetchPyritMitigation } from "../api/client";
import ExportPdfButton from "./ExportPdfButton";
import MitigationModal from "./MitigationModal";

function truncate(text, max = 2000) {
  if (!text || text.length <= max) return text;
  return text.slice(0, max) + "…";
}

export default function PyritResultPanel({ isRunning, error, result, elapsed = 0, meta = null }) {
  const [mitigation, setMitigation] = useState(null);

  async function openMitigation(objectiveId, title) {
    setMitigation({ title, loading: true, error: null, data: null });
    try {
      const data = await fetchPyritMitigation(objectiveId || "custom");
      setMitigation({ title, loading: false, error: null, data });
    } catch (err) {
      setMitigation({ title, loading: false, error: err.message, data: null });
    }
  }

  function closeMitigation() {
    setMitigation(null);
  }

  if (isRunning) {
    return (
      <section className="attack-path-panel results-empty">
        <p>Running multi-turn attack against target... {Math.round(elapsed)}s elapsed.</p>
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
        <p>Pick an objective on the left and click RUN to attack the target.</p>
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
        <h2>PyRIT run failed</h2>
        <pre>{result.error}</pre>
      </section>
    );
  }

  return (
    <section className="attack-path-panel">
      <div className="pyrit-summary">
        <div className="results-summary-head">
          <h2>Result — Multi-turn attack</h2>
          {meta && <ExportPdfButton engine="pyrit" result={result} meta={meta} />}
        </div>
        <p className="pyrit-objective">{result.objective}</p>
        <div className="results-stats">
          <div className="stat">
            <span className="stat-value">{result.executed_turns}</span>
            <span className="stat-label">Turns executed</span>
          </div>
          <div className={`stat ${result.achieved ? "stat-bad" : "stat-good"}`}>
            <span
              className={`pyrit-outcome-badge ${
                result.achieved ? "pyrit-outcome-bad" : "pyrit-outcome-good"
              }`}
            >
              {result.achieved ? "Objective achieved" : "Not achieved"}
            </span>
            <span className="stat-label">{result.outcome}</span>
          </div>
        </div>
        {result.final_score_rationale && (
          <div className="pyrit-rationale">
            <span className="attack-path-node-label">Scorer rationale</span>
            <p>{result.final_score_rationale}</p>
          </div>
        )}
        {result.achieved && (
          <button
            className="mitigation-button"
            onClick={() => openMitigation(result.objective_id, result.objective_id || "Custom objective")}
          >
            Mitigation
          </button>
        )}
      </div>

      {result.conversation.length === 0 ? (
        <p className="no-failures">No conversation was recorded.</p>
      ) : (
        <div className="conversation-list">
          {result.conversation.map((turn, idx) => (
            <div
              key={idx}
              className={`conversation-turn ${
                turn.role === "attacker" ? "conversation-attacker" : "conversation-target"
              }`}
            >
              <span className="conversation-role">
                {turn.role === "attacker" ? "Attacker" : "Target"} · turn {turn.turn}
              </span>
              <pre className="attack-path-node-body">{truncate(turn.text)}</pre>
            </div>
          ))}
        </div>
      )}

      {mitigation && (
        <MitigationModal
          title={mitigation.title}
          loading={mitigation.loading}
          error={mitigation.error}
          data={mitigation.data}
          onClose={closeMitigation}
        />
      )}
    </section>
  );
}
