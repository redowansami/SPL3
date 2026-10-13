import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchScanRunDetail } from "../api/client";
import AttackPathPanel from "./AttackPathPanel";
import PyritResultPanel from "./PyritResultPanel";

export default function ScanHistoryDetail() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setDetail(null);
    setError(null);
    setLoading(true);
    fetchScanRunDetail(runId)
      .then(setDetail)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [runId]);

  // ScanStatusResponse always has attack_paths; PyritScanStatusResponse always
  // has conversation — the two shapes are mutually exclusive, so this alone
  // tells us which live-result component to reuse.
  const isPyrit = detail != null && "conversation" in detail;

  const meta = detail && {
    targetUrl: detail.target_url,
    engine: detail.engine ?? (isPyrit ? "pyrit" : "garak"),
    runId: detail.run_id,
    startedAt: detail.started_at,
    endedAt: detail.ended_at,
  };

  return (
    <section className="history-detail">
      <button type="button" className="history-back-button" onClick={() => navigate("/history")}>
        ← Back to history
      </button>

      {loading ? (
        <section className="attack-path-panel results-empty">
          <p>Loading scan…</p>
        </section>
      ) : isPyrit ? (
        <PyritResultPanel
          isRunning={false}
          error={error}
          result={detail}
          elapsed={detail?.elapsed_seconds ?? 0}
          meta={meta}
        />
      ) : (
        <AttackPathPanel
          isRunning={false}
          error={error}
          result={detail}
          elapsed={detail?.elapsed_seconds ?? 0}
          meta={meta}
        />
      )}
    </section>
  );
}
