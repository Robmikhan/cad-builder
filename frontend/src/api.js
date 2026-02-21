const BASE = '/api';

export async function fetchJobs() {
  const res = await fetch(`${BASE}/jobs`);
  if (!res.ok) throw new Error(`Failed to fetch jobs: ${res.status}`);
  return res.json();
}

export async function fetchJob(jobId) {
  const res = await fetch(`${BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Failed to fetch job: ${res.status}`);
  return res.json();
}

export async function fetchJobEvents(jobId) {
  const res = await fetch(`${BASE}/jobs/${jobId}/events`);
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  return res.json();
}

export async function createJob(partSpec) {
  const res = await fetch(`${BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(partSpec),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create job: ${res.status}`);
  }
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${BASE}/models`);
  if (!res.ok) throw new Error(`Failed to fetch models: ${res.status}`);
  return res.json();
}

export function downloadBundleUrl(jobId) {
  return `${BASE}/assets/${jobId}/bundle`;
}
