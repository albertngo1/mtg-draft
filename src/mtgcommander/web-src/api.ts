// Every request the pages make goes through call(). Nothing else in these files talks to the server, so the
// timeout, the error kinds and the 202 answer ("the deck is still being prepared") are handled in one place.

import type { Preparing, Progress } from "./types.js";

export const TIMEOUT_MS = 10000;      // the page gives up on a request after this long
export const POLL_MS = 1000;          // how often it asks again while a deck is being prepared

export type ErrorKind = "unreachable" | "timeout" | "conflict" | "invalid" | "not_found" | "server";

/**
 * The one error type. `kind` says what to do about it:
 *   unreachable  the server did not answer at all (not running, wrong address, Tailscale off)
 *   timeout      it did not answer within TIMEOUT_MS (a change that took longer may still have been saved)
 *   conflict     409: the deck changed on another device; `details.revision` is where it is now
 *   invalid      400 or 422: the request breaks a rule; `message` says which, `details` lists the problems
 *   not_found    404: `details.suggestions` holds close names
 *   server       anything else (500 carries the server's own text, 403 the address check)
 */
export class ApiError extends Error {
  kind: ErrorKind;
  status: number;
  code: string | null;
  details: any;

  constructor(kind: ErrorKind, message: string, { status = 0, code = null, details = null }: { status?: number; code?: string | null; details?: unknown } = {}) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** True when the server never answered, so the request may or may not have arrived. */
  get cannotReach(): boolean {
    return this.kind === "unreachable" || this.kind === "timeout";
  }
}

/** A 2xx answer. A 202's body is the server's Preparing, whatever `T` says: check `status` before reading it. */
export interface Answer<T> {
  status: number;
  body: T;
}

const KIND_OF_STATUS: Record<number, ErrorKind> = { 400: "invalid", 404: "not_found", 409: "conflict", 422: "invalid" };

/**
 * One request. Resolves to {status, body} for any 2xx answer: 200 and 201 are done, and 202 is its own outcome
 * (the deck is still being prepared; `body.progress` says how far), not an error. Everything else throws ApiError.
 * `body` is sent as JSON when given.
 */
export async function call<T = any>(method: string, path: string, body?: unknown, { timeout = TIMEOUT_MS } = {}): Promise<Answer<T>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  let status = 0;
  let text = "";
  try {
    const response = await fetch(path, {
      method,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
      cache: "no-store",
    });
    status = response.status;
    text = await response.text();
  } catch (e) {
    if (controller.signal.aborted) {
      throw new ApiError("timeout", `The server did not answer within ${Math.round(timeout / 1000)} seconds.`);
    }
    throw new ApiError("unreachable", "The server did not answer.");
  } finally {
    clearTimeout(timer);
  }

  let data: any = null;
  try {
    data = JSON.parse(text);
  } catch (e) {
    data = null;
  }
  if (status >= 200 && status < 300) {
    if (data === null || typeof data !== "object") {
      throw new ApiError("server", `The server sent something that is not JSON (HTTP ${status}).`, { status });
    }
    return { status, body: data };
  }
  const error = data && typeof data === "object" ? data.error : null;
  if (error && typeof error === "object") {
    throw new ApiError(KIND_OF_STATUS[status] || "server", error.message || `The server answered HTTP ${status}.`,
      { status, code: error.code || null, details: error.details === undefined ? null : error.details });
  }
  const plain = text.trim().slice(0, 240);
  throw new ApiError("server", plain ? `HTTP ${status}: ${plain}` : `The server answered HTTP ${status}.`, { status });
}

export interface ReadyOptions {
  onProgress?: (progress: Progress | null, body: Preparing) => void;
  keepGoing?: () => boolean;
}

/**
 * call(), asking again every POLL_MS while the answer is 202. `onProgress(progress)` hears each 202's progress
 * ({requests, message}); `keepGoing()` returns false when nobody wants the answer any more (the person left the
 * screen), and the last 202 is then handed back for the caller to ignore. Only for routes where a 202 means "nothing
 * was done" (a read, a search, a change, suggestions); a PATCH's 202 means "saved", so it is never repeated.
 */
export async function callReady<T = any>(method: string, path: string, body?: unknown, { onProgress, keepGoing = () => true }: ReadyOptions = {}): Promise<Answer<T>> {
  for (;;) {
    const answer = await call<T>(method, path, body);
    if (answer.status !== 202) return answer;
    const preparing = answer.body as unknown as Preparing;
    if (onProgress) onProgress(preparing.progress || null, preparing);
    if (!keepGoing()) return answer;
    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
  }
}

// ---- addresses: names are encoded, because card names hold spaces, commas, apostrophes and "//"

const enc = encodeURIComponent;

export const deckPath = (player: string, id: string) => `/api/decks/${enc(player)}/${enc(id)}`;
export const deckKey = (player: string, id: string) => `${player}/${id}`;
export const cardSheetPath = (name: string, player: string, id: string) => `/api/cards/${enc(name)}?deck=${enc(deckKey(player, id))}`;
export const cardSearchPath = (text: string, player: string, id: string) => `/api/cards?q=${enc(text)}&deck=${enc(deckKey(player, id))}`;
