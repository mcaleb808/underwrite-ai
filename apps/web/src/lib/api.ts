import type {
  ApplicationStatus,
  CreateApplicationResponse,
  PersonaSummary,
} from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

export async function getApplication(taskId: string): Promise<ApplicationStatus> {
  const res = await fetch(`${API}/api/v1/applications/${taskId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`failed to load task ${taskId}: ${res.status}`);
  return res.json();
}

export function eventsUrl(taskId: string): string {
  return `${API}/api/v1/applications/${taskId}/events`;
}
