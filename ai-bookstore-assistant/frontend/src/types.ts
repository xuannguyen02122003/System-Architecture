// The shape of one execution-trace event, mirroring the backend's TraceEvent
// (see backend/app/events.py). Keeping this in sync is the "contract" between
// the two halves of the app.
export interface TraceEvent {
  seq: number;
  phase: string;
  label: string;
  status: "running" | "completed" | "failed" | "info";
  started_at: string;
  source?: string | null;
  query?: string | null;
  records_found?: number | null;
  duration_ms?: number | null;
  detail?: Record<string, unknown>;
}

// The final answer payload (the `answer` SSE event).
export interface AnswerPayload {
  question: string;
  intent: string;
  answer: string;
}

// A folded view-model for the trace panel: each pipeline step becomes one node
// whose state advances from "running" to "completed"/"failed" as events arrive.
export interface TraceNodeVM {
  id: number;
  phase: string;
  label: string;
  status: "running" | "completed" | "failed" | "info";
  source?: string | null;
  query?: string | null;
  records_found?: number | null;
  duration_ms?: number | null;
  detail?: Record<string, unknown>;
}

export type RunStatus = "idle" | "running" | "done" | "error";
