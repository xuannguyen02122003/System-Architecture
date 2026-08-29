import { useState } from "react";
import type { RunStatus, TraceEvent, TraceNodeVM } from "../types";
import { TraceNode } from "./TraceNode";

interface Props {
  nodes: TraceNodeVM[];
  rawEvents: TraceEvent[];
  status: RunStatus;
}

export function TracePanel({ nodes, rawEvents, status }: Props) {
  const [showRaw, setShowRaw] = useState(false);

  return (
    <section className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/50">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-slate-100">
            System Architecture · Execution Trace
          </h2>
          {status === "running" && (
            <span className="flex items-center gap-1 text-[11px] text-amber-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" />
              live
            </span>
          )}
        </div>
        {rawEvents.length > 0 && (
          <button
            onClick={() => setShowRaw((v) => !v)}
            className="rounded-md border border-slate-700 px-2 py-1 text-[11px] text-slate-400 transition hover:border-slate-500 hover:text-slate-200"
          >
            {showRaw ? "Hide" : "Raw"} events
          </button>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {nodes.length === 0 ? (
          <div className="flex h-full min-h-[16rem] flex-col items-center justify-center text-center">
            <div className="mb-3 text-3xl opacity-40">🧭</div>
            <p className="max-w-xs text-sm text-slate-500">
              Ask a question to see how the system analyzes it, chooses data
              sources, retrieves records, and composes the answer — one step at a
              time.
            </p>
          </div>
        ) : (
          <ol className="space-y-0">
            {nodes.map((node, i) => (
              <TraceNode key={node.id} node={node} isFirst={i === 0} />
            ))}
          </ol>
        )}

        {showRaw && (
          <pre className="mt-4 max-h-72 overflow-auto rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-[11px] leading-relaxed text-slate-400">
            {JSON.stringify(rawEvents, null, 2)}
          </pre>
        )}
      </div>
    </section>
  );
}
