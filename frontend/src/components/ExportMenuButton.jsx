import { useEffect, useRef, useState } from "react";

import { fetchMitigation, fetchPyritMitigation } from "../api/client";
import { generateScanReportCsv } from "../utils/csvReport";
import { generateScanReportPdf } from "../utils/pdfReport";

export default function ExportMenuButton({ engine, result, meta }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    function onClickOutside(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  async function handleExport(format) {
    setOpen(false);
    setLoading(true);
    setError(null);
    try {
      const mitigations = await collectMitigations(engine, result);
      const filenameBase = `atlas-scan-report-${meta.runId || "scan"}`;
      if (format === "pdf") {
        const doc = generateScanReportPdf({ meta, result, mitigations });
        doc.save(`${filenameBase}.pdf`);
      } else {
        const csv = generateScanReportCsv({ meta, result, mitigations });
        const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${filenameBase}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      setError(err.message || "Failed to generate export.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="export-menu-wrap" ref={wrapRef}>
      <button
        type="button"
        className="export-menu-toggle"
        onClick={() => setOpen((v) => !v)}
        disabled={loading}
        aria-haspopup="true"
        aria-expanded={open}
      >
        {loading ? "Preparing…" : "Download ▾"}
      </button>
      {open && (
        <ul className="export-menu-list" role="menu">
          <li>
            <button type="button" className="export-menu-item" role="menuitem" onClick={() => handleExport("pdf")}>
              Download PDF
            </button>
          </li>
          <li>
            <button type="button" className="export-menu-item" role="menuitem" onClick={() => handleExport("csv")}>
              Download CSV
            </button>
          </li>
        </ul>
      )}
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
