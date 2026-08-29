import type { AnswerPayload, RunStatus } from "../types";

const EXAMPLES = [
  "What books did Nguyen Van A buy in July?",
  "How many orders were placed in Q2 2026?",
  "What is the return policy?",
  "What science books do you have?",
  "What did Taylor Swift order?",
];

interface Props {
  question: string;
  setQuestion: (q: string) => void;
  onSubmit: (q: string) => void;
  answer: AnswerPayload | null;
  status: RunStatus;
  error: string | null;
  sources: string[];
}

export function ChatPanel({
  question,
  setQuestion,
  onSubmit,
  answer,
  status,
  error,
  sources,
}: Props) {
  const running = status === "running";

  return (
    <section className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/50">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-100">Ask a question</h2>
      </div>

      <div className="flex flex-col gap-4 p-4">
        {/* Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit(question);
          }}
          className="flex flex-col gap-2"
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSubmit(question);
              }
            }}
            rows={2}
            placeholder="e.g. What books did Nguyen Van A buy in July?"
            className="resize-none rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={running || !question.trim()}
            className="self-end rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
          >
            {running ? "Working…" : "Ask"}
          </button>
        </form>

        {/* Example chips */}
        <div>
          <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">
            Try an example
          </p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                disabled={running}
                onClick={() => {
                  setQuestion(ex);
                  onSubmit(ex);
                }}
                className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300 transition hover:border-indigo-500 hover:text-indigo-300 disabled:opacity-50"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        {/* Answer */}
        <div className="min-h-[7rem] rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          {error ? (
            <p className="text-sm text-rose-400">⚠ {error}</p>
          ) : answer ? (
            <div className="space-y-2">
              <span className="inline-block rounded-full bg-indigo-500/15 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-indigo-300">
                {answer.intent.replace(/_/g, " ")}
              </span>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-100">
                {answer.answer}
              </p>
              {sources.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 border-t border-slate-800 pt-3">
                  <span className="text-[11px] uppercase tracking-wide text-slate-500">
                    Data sources used
                  </span>
                  {sources.map((s) => (
                    <span
                      key={s}
                      className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[11px] text-sky-300"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : running ? (
            <p className="flex items-center gap-2 text-sm text-slate-400">
              <span className="h-2 w-2 animate-ping rounded-full bg-indigo-400" />
              Retrieving and composing the answer…
            </p>
          ) : (
            <p className="text-sm text-slate-500">
              The answer will appear here, grounded strictly in the store's data.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
