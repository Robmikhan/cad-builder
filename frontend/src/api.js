const BASE = '/api';

function authHeaders() {
  const key = localStorage.getItem('cad_api_key');
  return key ? { 'X-API-Key': key } : {};
}

export async function fetchJobs() {
  const res = await fetch(`${BASE}/jobs`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch jobs: ${res.status}`);
  return res.json();
}

export async function fetchJob(jobId) {
  const res = await fetch(`${BASE}/jobs/${jobId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch job: ${res.status}`);
  return res.json();
}

export async function fetchJobEvents(jobId) {
  const res = await fetch(`${BASE}/jobs/${jobId}/events`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  return res.json();
}

export async function createJob(partSpec) {
  const res = await fetch(`${BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(partSpec),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create job: ${res.status}`);
  }
  return res.json();
}

export async function uploadImage(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/upload`, {
    method: 'POST',
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${BASE}/models`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch models: ${res.status}`);
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}

export function downloadBundleUrl(jobId) {
  return `${BASE}/assets/${jobId}/bundle`;
}

export function downloadStepUrl(jobId) {
  return `${BASE}/assets/${jobId}/step`;
}

export function downloadStlUrl(jobId) {
  return `${BASE}/assets/${jobId}/stl`;
}

export function glbPreviewUrl(jobId) {
  return `${BASE}/assets/${jobId}/glb`;
}

export function subscribeToEvents(jobId, onEvent) {
  const url = `${BASE}/jobs/${jobId}/stream`;
  const es = new EventSource(url);
  es.onmessage = (e) => {
    try { onEvent(JSON.parse(e.data)); } catch {}
  };
  es.onerror = () => { es.close(); };
  return () => es.close();
}
