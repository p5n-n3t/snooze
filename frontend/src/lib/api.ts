import type { DashboardState, HistoryEntry, TaskDetail } from "./types";

export interface ControlRequest {
  action: string;
  target_id: string;
  values: Record<string, unknown>;
  expected_revision: number;
}

export interface ControlReceipt {
  status: "accepted" | "rejected" | "pending" | "confirmed" | string;
  message?: string;
  [key: string]: unknown;
}

type Fetcher = typeof fetch;

async function jsonRequest<T>(path: string, init?: RequestInit, fetcher: Fetcher = fetch): Promise<T> {
  const response = await fetcher(path, { credentials: "same-origin", ...init });
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`Snooze returned an unreadable response (${response.status}).`);
  }
  if (!response.ok) {
    const message = payload && typeof payload === "object" && "error" in payload
      ? String((payload as { error: unknown }).error)
      : `Request failed (${response.status}).`;
    throw new Error(message);
  }
  return payload as T;
}

export function getDashboardState(fetcher?: Fetcher): Promise<DashboardState> {
  return jsonRequest<DashboardState>("/api/v2/state", undefined, fetcher);
}

export function getTaskDetail(taskId: string, fetcher?: Fetcher): Promise<TaskDetail> {
  return jsonRequest<TaskDetail>(`/api/v2/tasks/${encodeURIComponent(taskId)}`, undefined, fetcher);
}

export function postLegacy(path: "/api/check" | "/api/ack" | "/api/settings", body: Record<string, unknown>, fetcher?: Fetcher) {
  return jsonRequest<{ ok: boolean }>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }, fetcher);
}

/**
 * The future control API returns its own acceptance/reconciliation receipt.
 * Callers must render that receipt verbatim; submission alone is never success.
 */
export function postControl(request: ControlRequest, fetcher?: Fetcher): Promise<ControlReceipt> {
  return jsonRequest<ControlReceipt>("/api/v2/control", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  }, fetcher);
}

interface LegacyWorker {
  id?: unknown;
  session_id?: unknown;
  state?: unknown;
  title?: unknown;
  name?: unknown;
  last_sent?: unknown;
  observed_at?: unknown;
}

interface LegacyIncident {
  job?: unknown;
  kind?: unknown;
  message?: unknown;
  at?: unknown;
}

/** Normalize the existing private history endpoint at the API boundary. */
export async function getHistory(fetcher?: Fetcher): Promise<HistoryEntry[]> {
  const snapshot = await jsonRequest<{ workers?: LegacyWorker[]; incidents?: LegacyIncident[] }>("/api/state", undefined, fetcher);
  const rows: HistoryEntry[] = [];
  const terminal = new Set(["complete", "completed", "done", "cancelled", "canceled", "failed"]);
  for (const worker of snapshot.workers ?? []) {
    const state = typeof worker.state === "string" ? worker.state.toLowerCase() : "";
    if (!terminal.has(state)) continue;
    const taskId = typeof worker.id === "string" ? worker.id : null;
    rows.push({
      id: `task:${taskId ?? rows.length}`,
      at: finiteTimestamp(worker.observed_at) ?? finiteTimestamp(worker.last_sent),
      kind: state,
      title: stringValue(worker.title) ?? stringValue(worker.name) ?? taskId ?? "Task outcome",
      detail: "Recorded task state from local Snooze history. Imported usage and validation detail are unavailable.",
      task_id: taskId,
    });
  }
  for (const incident of snapshot.incidents ?? []) {
    rows.push({
      id: `incident:${rows.length}`,
      at: finiteTimestamp(incident.at),
      kind: stringValue(incident.kind) ?? "incident",
      title: stringValue(incident.job) ?? "Worker event",
      detail: stringValue(incident.message) ?? "No event detail was recorded.",
      task_id: stringValue(incident.job),
    });
  }
  return rows.sort((a, b) => (b.at ?? 0) - (a.at ?? 0));
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function finiteTimestamp(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
