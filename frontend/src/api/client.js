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
