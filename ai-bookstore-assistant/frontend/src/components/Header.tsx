export function Header() {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 lg:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/15 text-lg">
            📚
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-slate-100">
              Chapter One Books · AI Data Assistant
            </h1>
            <p className="text-xs text-slate-400">
              Ask a question and watch the system retrieve the answer, step by step.
            </p>
          </div>
        </div>
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="hidden rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 transition hover:border-slate-500 hover:text-slate-100 sm:block"
        >
          API ↗
        </a>
      </div>
    </header>
  );
}
