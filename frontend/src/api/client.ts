import type {
  CancelJobResponse,
  DirectoryContent,
  JobStatus,
  MediaNode,
  ProcessRequest,
  ProcessResponse,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function fetchTree(): Promise<MediaNode> {
  const res = await fetch(`${API_URL}/tree`);
  if (!res.ok) throw new Error("Failed to fetch tree");
  return res.json() as Promise<MediaNode>;
}

export async function fetchList(dirVal: string): Promise<DirectoryContent> {
  const params = new URLSearchParams({ dir: dirVal });
  const res = await fetch(`${API_URL}/list?${params}`);
  if (!res.ok) throw new Error("Failed to fetch list");
  return res.json() as Promise<DirectoryContent>;
}

export async function startProcess(payload: ProcessRequest): Promise<ProcessResponse> {
  const res = await fetch(`${API_URL}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to start process");
  return res.json() as Promise<ProcessResponse>;
}

export async function fetchJob(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch job");
  return res.json() as Promise<JobStatus>;
}

export function getJobEventsUrl(jobId: string) {
  return `${API_URL}/jobs/${jobId}/events`;
}

export function getJobsListEventsUrl() {
  return `${API_URL}/jobs/events`;
}

export async function cancelJob(jobId: string): Promise<CancelJobResponse> {
  const res = await fetch(`${API_URL}/jobs/${jobId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to cancel job");
  return res.json() as Promise<CancelJobResponse>;
}
