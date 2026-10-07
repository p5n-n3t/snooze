export interface Account {
  server_key: string | null;
  label: string | null;
  capacity: number | null;
  enabled: boolean | null;
}

export interface Slot {
  task_id: string | null;
  session_id: string | null;
  account_id: string | null;
  logical_slot: number | null;
  workspace_id: string | null;
  task_summary: string | null;
  requested_model: string | null;
  confirmed_model: string | null;
  requested_effort: string | null;
  confirmed_effort: string | null;
  started_at: number | null;
  observed_at: number | null;
  provider_state: string | null;
  task_state: string | null;
  observation_freshness: string | null;
  references: string[];
}

export interface Incident {
  task_id: string | null;
  kind: string | null;
  message: string | null;
  at: number | null;
}

export interface Capability {
  supported: boolean;
  reason: string;
}

export interface DashboardState {
  schema_version: 2;
  project: { id: string; name: string };
  summary: { active_tasks: number; incidents: number };
  accounts: Account[];
  slots: Slot[];
  incidents: Incident[];
  settings: { interval: number | null };
  capabilities: { dispatch: Capability; [key: string]: Capability };
  cycle: { started_at: number | null; finished_at: number | null; checked: number | null };
}

export interface TaskDetail {
  task_id: string;
  summary: string | null;
  instruction: string | null;
  state: string | null;
  attempts: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
  references: string[];
}

export interface HistoryEntry {
  id: string;
  at: number | null;
  kind: string;
  title: string;
  detail: string;
  task_id: string | null;
}

export type PageKey = "watch" | "queue" | "providers" | "history" | "settings";
