import { useState } from "react";

import { fetchMitigation, fetchPyritMitigation } from "../api/client";
import { generateScanReportPdf } from "../utils/pdfReport";

export default function ExportPdfButton({ engine, result, meta }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleExport() {
    setLoading(true);
    setError(null);
    try {
      const mitigations = await collectMitigations(engine, result);
      const doc = generateScanReportPdf({ meta, result, mitigations });
      doc.save(`atlas-scan-report-${meta.runId || "scan"}.pdf`);
    } catch (err) {
      setError(err.message || "Failed to generate PDF.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="export-pdf-wrap">
      <button type="button" className="export-pdf-button" onClick={handleExport} disabled={loading}>
        {loading ? "Preparing PDF…" : "Download PDF"}
      </button>
      {error && <span className="export-pdf-error">{error}</span>}
    </div>
  );
}

async function collectMitigations(engine, result) {
  if (engine === "pyrit") {
    if (!result.achieved) return [];
    const objectiveId = result.objective_id || "custom";
    const data = await fetchPyritMitigation(objectiveId);
    return [{ label: result.objective_id || "Custom objective", ...data }];
  }

  const probes = [...new Set((result.attack_paths || []).map((item) => item.probe))];
  const mitigations = await Promise.all(
    probes.map(async (probe) => {
      const data = await fetchMitigation(probe);
      return { label: probe, ...data };
    })
  );
  return mitigations;
}
