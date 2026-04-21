import type {
  ApplicantProfile,
  ApplicationListItem,
  ApplicationStatus,
  CreateApplicationResponse,
  DecisionPayload,
  District,
  PersonaSummary,
  Verdict,
} from "./types";

// Server-side renders use INTERNAL_API_URL (docker service hostname);
// the browser uses the publicly-reachable NEXT_PUBLIC_API_URL.
const API =
  typeof window === "undefined"
    ? (process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

export async function listPersonas(): Promise<PersonaSummary[]> {
  const res = await fetch(`${API}/api/v1/personas`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to load personas: ${res.status}`);
  return res.json();
}

export async function getPersona(id: string): Promise<unknown> {
  const res = await fetch(`${API}/api/v1/personas/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to load persona ${id}: ${res.status}`);
  return res.json();
}

export async function createApplicationFromPersona(
  personaId: string,
): Promise<CreateApplicationResponse> {
  const applicant = await getPersona(personaId);
  const form = new FormData();
  form.append("applicant", JSON.stringify(applicant));
  const res = await fetch(`${API}/api/v1/applications`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`failed to create application: ${res.status} ${body}`);
  }
  return res.json();
}

export async function createApplication(
  profile: ApplicantProfile,
  files: File[],
): Promise<CreateApplicationResponse> {
  const form = new FormData();
  form.append("applicant", JSON.stringify(profile));
  for (const file of files) {
    form.append("medical_docs", file);
  }
  const res = await fetch(`${API}/api/v1/applications`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`failed to create application: ${res.status} ${body}`);
  }
  return res.json();
}

export async function listDistricts(): Promise<District[]> {
  const res = await fetch(`${API}/api/v1/districts`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to list districts: ${res.status}`);
  return res.json();
}

export async function getApplication(taskId: string): Promise<ApplicationStatus> {
  const res = await fetch(`${API}/api/v1/applications/${taskId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`failed to load task ${taskId}: ${res.status}`);
  return res.json();
}

export async function listApplications(limit = 20): Promise<ApplicationListItem[]> {
  const res = await fetch(`${API}/api/v1/applications?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`failed to list applications: ${res.status}`);
  return res.json();
}

export async function listFiles(taskId: string): Promise<string[]> {
  const res = await fetch(`${API}/api/v1/applications/${taskId}/files`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`failed to list files: ${res.status}`);
  return res.json();
}

export function fileUrl(taskId: string, filename: string): string {
  return `${API}/api/v1/applications/${taskId}/files/${encodeURIComponent(filename)}`;
}

export function eventsUrl(taskId: string): string {
  return `${API}/api/v1/applications/${taskId}/events`;
}

export type ModifyDecisionPatch = {
  verdict?: Verdict;
  premium_loading_pct?: number;
  conditions?: string[];
  reasoning?: string;
};

export async function modifyDecision(
  taskId: string,
  patch: ModifyDecisionPatch,
): Promise<ApplicationStatus> {
  const res = await fetch(`${API}/api/v1/applications/${taskId}/decision`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error(`failed to modify: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function approveDecision(
  taskId: string,
  approvedBy: string,
  notifyEmail?: string,
): Promise<{ status: string; email_status: string; provider_message_id: string | null }> {
  const res = await fetch(`${API}/api/v1/applications/${taskId}/approve`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ approved_by: approvedBy, notify_email: notifyEmail }),
  });
  if (!res.ok) throw new Error(`failed to approve: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function reevaluate(
  taskId: string,
  note?: string,
): Promise<{ task_id: string; status: string }> {
  const res = await fetch(`${API}/api/v1/applications/${taskId}/reeval`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ note }),
  });
  if (!res.ok) throw new Error(`failed to reeval: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function cancelApplication(taskId: string): Promise<void> {
  const res = await fetch(`${API}/api/v1/applications/${taskId}/cancel`, { method: "POST" });
  if (!res.ok) throw new Error(`failed to cancel: ${res.status} ${await res.text()}`);
}

export async function deleteApplication(taskId: string): Promise<void> {
  const res = await fetch(`${API}/api/v1/applications/${taskId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`failed to delete: ${res.status} ${await res.text()}`);
}

export async function clearTerminalApplications(): Promise<void> {
  const res = await fetch(`${API}/api/v1/applications`, { method: "DELETE" });
  if (!res.ok) throw new Error(`failed to clear: ${res.status} ${await res.text()}`);
}

export type { DecisionPayload };
