import type { TraceNodeVM } from "../types";

// Human-friendly names for the pipeline phases.
const PHASE_LABELS: Record<string, string> = {
  REQUEST_RECEIVED: "Request received",
  QUERY_ANALYSIS: "Query analysis",
  SOURCE_SELECTION: "Source selection",
  DATA_RETRIEVAL: "Data retrieval",
  ANSWER_GENERATION: "Answer generation",
  COMPLETED: "Completed",
  NOT_FOUND: "Not found",
  ERROR: "Error",
};

function StatusIcon({ node }: { node: TraceNodeVM }) {
  if (node.status === "running") {
    return (
      <span className="block h-4 w-4 animate-spin rounded-full border-2 border-amber-400/30 border-t-amber-400" />
    );
  }
  if (node.status === "failed" || node.phase === "ERROR") {
    return <span className="text-rose-400">✕</span>;
  }
  if (node.phase === "NOT_FOUND") {
    return <span className="text-amber-400">⚠</span>;
  }
  if (node.status === "completed") {
    return <span className="text-emerald-400">✓</span>;
  }
  // info markers (request received / completed)
  return <span className="text-indigo-400">●</span>;
}

// Accent colors keyed to the node's state.
function accent(node: TraceNodeVM): string {
  if (node.status === "running") return "border-amber-500/40 bg-amber-500/[0.06]";
  if (node.status === "failed" || node.phase === "ERROR")
    return "border-rose-500/40 bg-rose-500/[0.06]";
  if (node.phase === "NOT_FOUND") return "border-amber-500/40 bg-amber-500/[0.06]";
  return "border-slate-700 bg-slate-900/40";
}

export function TraceNode({ node, isFirst }: { node: TraceNodeVM; isFirst: boolean }) {
  const phaseLabel = PHASE_LABELS[node.phase] ?? node.phase;

  return (
    <li className="animate-node-in list-none">
      {!isFirst && <div className="ml-[1.15rem] h-4 w-px animate-line bg-slate-700" />}

      <div className={`flex gap-3 rounded-lg border p-3 ${accent(node)}`}>
        <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center text-sm">
          <StatusIcon node={node} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              {phaseLabel}
            </span>
            {node.duration_ms != null && (
              <span className="shrink-0 text-[10px] text-slate-500">
                {node.duration_ms} ms
              </span>
            )}
          </div>

          <p className="mt-0.5 text-sm text-slate-100">{node.label}</p>

          {(node.source || node.query || node.records_found != null) && (
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {node.source && (
                <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[11px] text-sky-300">
                  {node.source}
                </span>
              )}
              {node.query && (
                <code className="max-w-full truncate rounded bg-slate-950 px-1.5 py-0.5 font-mono text-[11px] text-slate-400">
                  {node.query}
                </code>
              )}
              {node.records_found != null && (
                <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                  {node.records_found} record{node.records_found === 1 ? "" : "s"}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </li>
  );
}
