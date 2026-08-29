import type { TraceEvent, AnswerPayload } from "./types";

// Where the backend lives. Override with VITE_API_BASE in a .env file if needed.
const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://127.0.0.1:8000";

export interface StreamHandlers {
  onTrace: (event: TraceEvent) => void;
  onAnswer: (answer: AnswerPayload) => void;
  onError: (message: string) => void;
  onDone: () => void;
}

/**
 * POST a question and consume the Server-Sent Events stream.
 *
 * We use fetch + a streaming reader (rather than the browser's EventSource)
 * because EventSource only supports GET requests, and we want to send the
 * question in a POST body. We read the response body chunk by chunk, split it
 * into SSE messages on the blank-line delimiter, and dispatch each one.
 */
export async function askQuestion(
  question: string,
  handlers: StreamHandlers
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
  } catch (err) {
    handlers.onError(
      `Could not reach the server at ${API_BASE}. Is the backend running?`
    );
    handlers.onDone();
    return;
  }

  if (!response.ok || !response.body) {
    handlers.onError(`Server responded with status ${response.status}.`);
    handlers.onDone();
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE messages are separated by a blank line ("\n\n").
    let separatorIndex: number;
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawMessage = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);
      dispatchMessage(rawMessage, handlers);
    }
  }

  handlers.onDone();
}

function dispatchMessage(raw: string, handlers: StreamHandlers): void {
  let eventType = "message";
  let data = "";

  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) eventType = line.slice(6).trim();
    else if (line.startsWith("data:")) data = line.slice(5).trim();
  }
  if (!data) return;

  let parsed: unknown;
  try {
    parsed = JSON.parse(data);
  } catch {
    return; // ignore malformed chunks
  }

  if (eventType === "trace") handlers.onTrace(parsed as TraceEvent);
  else if (eventType === "answer") handlers.onAnswer(parsed as AnswerPayload);
  else if (eventType === "error")
    handlers.onError((parsed as { message?: string }).message ?? "Unknown error");
}
