function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString();
}

function formatDuration(startedAt, endedAt) {
  if (!startedAt || !endedAt) return "—";
  const start = new Date(startedAt).getTime();
  const end = new Date(endedAt).getTime();
  if (Number.isNaN(start) || Number.isNaN(end)) return "—";
  const seconds = Math.max(0, (end - start) / 1000);
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const rest = Math.round(seconds % 60);
  return `${minutes}m ${rest}s`;
}

function csvField(value) {
  if (value == null) return "";
  const str = String(value);
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function csvRow(fields) {
  return fields.map(csvField).join(",") + "\r\n";
}

function buildMetaBlock(meta, result, isPyrit) {
  const engineLabel = isPyrit ? "PyRIT (multi-turn)" : "Garak";
  const status = result.status ?? (result.ok ? "completed" : "failed");

  let out = "";
  out += csvRow(["ATLAS-Scan Report"]);
  out += csvRow(["Target URL", meta.targetUrl || "—"]);
  out += csvRow(["Attack Engine", engineLabel]);
  out += csvRow(["Status", String(status)]);
  out += csvRow(["Run ID", meta.runId || "—"]);
  out += csvRow(["Scan Started", formatDate(meta.startedAt)]);
  out += csvRow(["Scan Ended", formatDate(meta.endedAt)]);
  out += csvRow(["Duration", formatDuration(meta.startedAt, meta.endedAt)]);
  out += csvRow(["Generated", formatDate(new Date())]);

  if (isPyrit) {
    out += csvRow(["Turns Executed", String(result.executed_turns ?? 0)]);
    out += csvRow(["Objective Achieved", result.achieved ? "Yes" : "No"]);
    out += csvRow(["Outcome", result.outcome ?? "—"]);
  } else {
    const attempts = result.attempts_evaluated ?? 0;
    const failures = result.failure_count ?? 0;
    out += csvRow(["Attempts Evaluated", String(attempts)]);
    out += csvRow(["Failures Found (Successful Exploits)", String(failures)]);
    out += csvRow(["Clean Attempts", String(Math.max(0, attempts - failures))]);
  }

  out += "\r\n";
  return out;
}

function buildGarakSection(result) {
  let out = csvRow(["Attack Path"]);
  out += csvRow([
    "#",
    "Goal / Technique",
    "Probe",
    "Detector",
    "Injected Prompt (all turns)",
    "Target Output",
    "Triggers",
    "Score",
    "NLI Verdict",
  ]);

  const paths = result.attack_paths || [];
  for (const item of paths) {
    out += csvRow([
      item.attempt_seq,
      item.goal || "—",
      item.probe || "—",
      item.detector || "—",
      (item.prompt_turns || []).join("\n---\n"),
      item.output || "",
      (item.triggers || []).join(", "),
      item.score != null ? item.score.toFixed(2) : "—",
      item.nli_verdict || "—",
    ]);
  }
  if (paths.length === 0) {
    out += csvRow(["No successful attack paths were found for this probe."]);
  }

  out += "\r\n";
  return out;
}

function buildPyritSection(result) {
  let out = csvRow(["Attack Turns"]);
  if (result.final_score_rationale) {
    out += csvRow(["Scorer Rationale", result.final_score_rationale]);
  }
  out += csvRow(["Turn", "Role", "Message"]);

  const turns = result.conversation || [];
  for (const t of turns) {
    out += csvRow([t.turn, t.role === "attacker" ? "Attacker" : "Target", t.text || ""]);
  }
  if (turns.length === 0) {
    out += csvRow(["No conversation was recorded."]);
  }

  out += "\r\n";
  return out;
}

function buildMitigationsSection(mitigations) {
  let out = csvRow(["Mitigations"]);
  out += csvRow(["Probe / Objective", "ATLAS Techniques", "ATLAS Mitigations", "Strategies"]);

  if (!mitigations || mitigations.length === 0) {
    out += csvRow(["No mitigations required — no successful exploits were found."]);
    return out;
  }

  for (const m of mitigations) {
    const techniques = (m.atlas_techniques || []).map((t) => `${t.id} ${t.name}`).join("; ") || "—";
    const mitigationText =
      (m.atlas_mitigations || []).map((mit) => `${mit.id} ${mit.name}: ${mit.description}`).join(" | ") || "—";
    const strategies = (m.strategies || []).join("; ") || "—";
    out += csvRow([m.label || m.garak_probe || m.objective_id || "—", techniques, mitigationText, strategies]);
  }

  return out;
}

export function generateScanReportCsv({ meta, result, mitigations }) {
  const isPyrit = "conversation" in result;

  let csv = buildMetaBlock(meta, result, isPyrit);
  csv += isPyrit ? buildPyritSection(result) : buildGarakSection(result);
  csv += buildMitigationsSection(mitigations);

  return csv;
}
