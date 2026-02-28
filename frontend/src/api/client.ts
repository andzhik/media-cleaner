const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function fetchTree() {
  const res = await fetch(`${API_URL}/tree`);
  if (!res.ok) throw new Error("Failed to fetch tree");
  return res.json();
}

export async function fetchList(dirVal: string) {
  const params = new URLSearchParams({ dir: dirVal });
  const res = await fetch(`${API_URL}/list?${params}`);
  if (!res.ok) throw new Error("Failed to fetch list");
  return res.json();
}

export async function startProcess(payload: any) {
  const res = await fetch(`${API_URL}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to start process");
  return res.json();
}

export async function fetchJob(jobId: string) {
  const res = await fetch(`${API_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch job");
  return res.json();
}

export function getJobEventsUrl(jobId: string) {
  return `${API_URL}/jobs/${jobId}/events`;
}

export function getJobsUrl() {
  return `${API_URL}/jobs`;
}
