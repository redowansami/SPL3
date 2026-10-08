const API_BASE = "http://localhost:8000";

export async function fetchProbes() {
  const res = await fetch(`${API_BASE}/api/probes`);
  if (!res.ok) {
    throw new Error(`Failed to load probes (${res.status})`);
  }
  return res.json();
}

export async function startScan({ targetUrl, probeId, engine, requestTemplate, responseField }) {
  const res = await fetch(`${API_BASE}/api/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_url: targetUrl,
      probe_id: probeId,
      engine,
      request_template: requestTemplate ?? null,
      response_field: responseField?.trim() ? responseField.trim() : null,
    }),
  });

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || `Scan request failed (${res.status})`);
  }
  return data;
}

export async function getScanStatus(runId) {
  const res = await fetch(`${API_BASE}/api/scan/${runId}`);
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || `Status check failed (${res.status})`);
  }
  return data;
}

export async function cancelScan(runId) {
  const res = await fetch(`${API_BASE}/api/scan/${runId}/cancel`, { method: "POST" });
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || `Cancel failed (${res.status})`);
  }
  return data;
}

export async function fetchMitigation(garakProbe) {
  const res = await fetch(`${API_BASE}/api/mitigations/${encodeURIComponent(garakProbe)}`);
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || `Failed to load mitigation (${res.status})`);
  }
  return data;
}

// ---- PyRIT multi-turn attacks (parallel to the garak scan endpoints) ----

export async function fetchObjectives() {
  const res = await fetch(`${API_BASE}/api/pyrit/objectives`);
  if (!res.ok) {
    throw new Error(`Failed to load objectives (${res.status})`);
  }
  return res.json();
}

export async function startPyritScan({ targetUrl, objectiveId, maxTurns, requestTemplate, responseField }) {
  const res = await fetch(`${API_BASE}/api/pyrit/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_url: targetUrl,
      objective_id: objectiveId,
      max_turns: maxTurns ?? null,
      request_template: requestTemplate ?? null,
      response_field: responseField?.trim() ? responseField.trim() : null,
    }),
  });

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || `PyRIT scan request failed (${res.status})`);
  }
  return data;
}

export async function getPyritScanStatus(runId) {
  const res = await fetch(`${API_BASE}/api/pyrit/scan/${runId}`);
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || `Status check failed (${res.status})`);
  }
  return data;
}

export async function cancelPyritScan(runId) {
  const res = await fetch(`${API_BASE}/api/pyrit/scan/${runId}/cancel`, { method: "POST" });
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || `Cancel failed (${res.status})`);
  }
  return data;
}

export async function fetchPyritMitigation(objectiveId) {
  const res = await fetch(`${API_BASE}/api/pyrit/mitigations/${encodeURIComponent(objectiveId)}`);
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(data?.detail || `Failed to load mitigation (${res.status})`);
  }
  return data;
}
