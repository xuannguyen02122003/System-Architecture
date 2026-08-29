import { useCallback, useState } from "react";
import { askQuestion } from "./api";
import type { AnswerPayload, RunStatus, TraceEvent, TraceNodeVM } from "./types";
import { Header } from "./components/Header";
import { ChatPanel } from "./components/ChatPanel";
import { TracePanel } from "./components/TracePanel";

/**
 * Fold a stream of raw events into a list of pipeline "nodes".
 *
 * Each step emits a "running" event then a "completed"/"failed" event. We turn
 * the first into a new node and let the second update it in place — that's what
 * produces the "spinner -> green check" effect. One-shot markers (info) become
 * their own nodes.
 */
function reduceEvent(nodes: TraceNodeVM[], ev: TraceEvent): TraceNodeVM[] {
  if (ev.status === "running") {
    return [
      ...nodes,
      { id: ev.seq, phase: ev.phase, label: ev.label, status: "running", source: ev.source },
    ];
  }

  if (ev.status === "completed" || ev.status === "failed") {
    const next = [...nodes];
    // Update the most recent still-running node (steps don't overlap here).
    for (let i = next.length - 1; i >= 0; i--) {
      if (next[i].status === "running") {
        next[i] = {
          ...next[i],
          status: ev.status,
          query: ev.query,
          records_found: ev.records_found,
          duration_ms: ev.duration_ms,
          detail: ev.detail,
          source: ev.source ?? next[i].source,
        };
        break;
      }
    }
    return next;
  }

  // info marker (REQUEST_RECEIVED, NOT_FOUND, COMPLETED)
  return [
    ...nodes,
    { id: ev.seq, phase: ev.phase, label: ev.label, status: "info", detail: ev.detail },
  ];
}

export default function App() {
  const [question, setQuestion] = useState("");
  const [nodes, setNodes] = useState<TraceNodeVM[]>([]);
  const [rawEvents, setRawEvents] = useState<TraceEvent[]>([]);
  const [answer, setAnswer] = useState<AnswerPayload | null>(null);
  const [status, setStatus] = useState<RunStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    (q: string) => {
      const text = q.trim();
      if (!text || status === "running") return;

      // Reset for a fresh run.
      setNodes([]);
      setRawEvents([]);
      setAnswer(null);
      setError(null);
      setStatus("running");

      askQuestion(text, {
        onTrace: (ev) => {
          setRawEvents((prev) => [...prev, ev]);
          setNodes((prev) => reduceEvent(prev, ev));
        },
        onAnswer: (a) => setAnswer(a),
        onError: (msg) => {
          setError(msg);
          setStatus("error");
        },
        onDone: () => setStatus((s) => (s === "error" ? "error" : "done")),
      }).catch((err) => {
        setError(String(err));
        setStatus("error");
      });
    },
    [status]
  );

  // Which data sources the trace actually touched — shown under the answer.
  const sourcesUsed = Array.from(
    new Set(nodes.filter((n) => n.source).map((n) => n.source as string))
  );

  return (
    <div className="min-h-full bg-slate-950 text-slate-200">
      <Header />
      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-4 p-4 lg:grid-cols-2 lg:gap-6 lg:p-6">
        <ChatPanel
          question={question}
          setQuestion={setQuestion}
          onSubmit={submit}
          answer={answer}
          status={status}
          error={error}
          sources={sourcesUsed}
        />
        <TracePanel nodes={nodes} rawEvents={rawEvents} status={status} />
      </main>
    </div>
  );
}
