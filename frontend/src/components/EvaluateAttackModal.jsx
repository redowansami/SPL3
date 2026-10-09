import { useState } from "react";

import { fetchPyritMitigation } from "../api/client";
import MitigationModal from "./MitigationModal";

export default function EvaluateAttackModal({ onEvaluate, onClose }) {
  const [objective, setObjective] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [mitigation, setMitigation] = useState(null);

  async function handleEvaluate() {
    if (!objective.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const data = await onEvaluate(objective.trim());
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function openMitigation() {
    const title = result.objective_id || "Custom objective";
    setMitigation({ title, loading: true, error: null, data: null });
    try {
      const data = await fetchPyritMitigation(result.objective_id || "custom");
      setMitigation({ title, loading: false, error: null, data });
    } catch (err) {
      setMitigation({ title, loading: false, error: err.message, data: null });
    }
  }

  return (
    <div className="mitigation-modal-overlay" onClick={onClose}>
      <div className="mitigation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="mitigation-modal-header">
          <h3>Evaluate attack</h3>
          <button className="mitigation-modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="mitigation-modal-body">
          <div className="mitigation-section">
            <span className="mitigation-section-label">What was your objective?</span>
            <textarea
              className="request-template-input evaluate-objective-input"
              rows={3}
              placeholder="e.g. make the target reveal the admin password"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              disabled={loading}
            />
          </div>

          <button
            type="button"
            className="mitigation-button"
            disabled={!objective.trim() || loading}
            onClick={handleEvaluate}
          >
            {loading ? "Evaluating…" : "Evaluate"}
          </button>

          {error && <p className="mitigation-modal-status mitigation-modal-error">{error}</p>}

          {result && (
            <div className="results-stats">
              <div className={`stat ${result.achieved ? "stat-bad" : "stat-good"}`}>
                <span
                  className={`pyrit-outcome-badge ${
                    result.achieved ? "pyrit-outcome-bad" : "pyrit-outcome-good"
                  }`}
                >
                  {result.achieved ? "Objective achieved" : "Not achieved"}
                </span>
              </div>
              {result.rationale && (
                <div className="pyrit-rationale">
                  <span className="attack-path-node-label">Scorer rationale</span>
                  <p>{result.rationale}</p>
                </div>
              )}
              {result.achieved && (
                <button type="button" className="mitigation-button" onClick={openMitigation}>
                  Mitigation
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {mitigation && (
        <MitigationModal
          title={mitigation.title}
          loading={mitigation.loading}
          error={mitigation.error}
          data={mitigation.data}
          onClose={() => setMitigation(null)}
        />
      )}
    </div>
  );
}
