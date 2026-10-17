// The hash router, the state store, and "draw the screen from the current state". Each screen module turns the state into
// elements; this file decides which screen that is, loads what it needs, and sends every change to the server one at a time.
//
// The pages never work out a metric. Every number on screen came in an answer from the server (api.js); the code only
// lays numbers out: sorting, folding and formatting.

import { call, callReady, ApiError, deckPath, deckKey } from "./api.js";
import * as ui from "./ui.js";
import * as decksScreen from "./decks.js";
import * as deckScreen from "./deck.js";
import * as cardSheet from "./card.js";
import * as addSheet from "./add.js";
import type { DeckAnswer, Progress, Settings } from "./types.js";

const PLAYER_KEY = "mtg-commander-player";
const WIDE = window.matchMedia("(min-width: 1024px)");

// ------------------------------------------------------------------------------------------------ the chosen player
// The only thing kept on this device. Every read and write is guarded: the pages work with storage blocked or full.

function readPlayer(): string | null {
  try {
    return localStorage.getItem(PLAYER_KEY) || null;
  } catch (e) {
    return null;
  }
}

function writePlayer(name: string | null): void {
  try {
    if (name) localStorage.setItem(PLAYER_KEY, name);
    else localStorage.removeItem(PLAYER_KEY);
  } catch (e) {
    // private mode or blocked storage: the choice is simply not remembered
  }
}

// -------------------------------------------------------------------------------------------------------------- routes
//   #/                              Decks                 #/new, #/new?base=ID        New version
//   #/new-base                      New base deck         #/d/PLAYER/ID               a deck (Cards)
//   #/d/PLAYER/ID/metrics | changes | suggestions          the other tabs
//   #/d/PLAYER/ID/card/NAME         a card's sheet        #/d/PLAYER/ID/add           the Add a card sheet
// Names are encoded with encodeURIComponent, because card names hold spaces, commas, apostrophes and "//".

const enc = encodeURIComponent;
const TABS = ["cards", "metrics", "changes", "suggestions"] as const;

export type Tab = (typeof TABS)[number];
export type SheetRoute = { kind: "card"; name: string; cut?: undefined; card?: undefined } | AddRoute;
export interface AddRoute { kind: "add"; cut: string; card: string; name?: undefined }
export interface DeckRoute { name: "deck"; player: string; id: string; tab: Tab | null; sheet: SheetRoute | null; query: Record<string, string> }
export type Route = { name: "decks" | "new" | "new-base"; query: Record<string, string>; sheet?: undefined } | DeckRoute;

function decode(part: string): string {
  try {
    return decodeURIComponent(part);
  } catch (e) {
    return part;
  }
}

export function parseRoute(hash: string): Route {
  const [path, queryText = ""] = String(hash || "").replace(/^#/, "").split("?");
  const parts = path.split("/").map(decode);
  while (parts.length && parts[0] === "") parts.shift();
  while (parts.length && parts[parts.length - 1] === "") parts.pop();
  const query = Object.fromEntries(new URLSearchParams(queryText));
  if (parts[0] === "new" && parts.length === 1) return { name: "new", query };
  if (parts[0] === "new-base" && parts.length === 1) return { name: "new-base", query };
  if (parts[0] === "d" && parts.length >= 3) {
    const [, player, id, ...rest] = parts;
    const route: DeckRoute = { name: "deck", player, id, tab: null, sheet: null, query };
    if (rest.length === 0) route.tab = "cards";
    else if (rest.length === 1 && (TABS as readonly string[]).includes(rest[0])) route.tab = rest[0] as Tab;
    else if (rest[0] === "card" && rest.length >= 2) route.sheet = { kind: "card", name: rest.slice(1).join("/") };
    else if (rest.length === 1 && rest[0] === "add") route.sheet = { kind: "add", cut: query.cut || "", card: query.card || "" };
    else route.tab = "cards";
    return route;
  }
  return { name: "decks", query };
}

const link = {
  decks: "#/",
  newVersion: (baseId?: string) => (baseId ? `#/new?base=${enc(baseId)}` : "#/new"),
  newBase: "#/new-base",
  deck: (player: string, id: string, tab: Tab = "cards") => `#/d/${enc(player)}/${enc(id)}${tab === "cards" ? "" : `/${tab}`}`,
  card: (player: string, id: string, name: string) => `#/d/${enc(player)}/${enc(id)}/card/${enc(name)}`,
  add: (player: string, id: string, params: Record<string, string> = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return `#/d/${enc(player)}/${enc(id)}/add${query ? `?${query}` : ""}`;
  },
};

// --------------------------------------------------------------------------------------------------------------- state

/** The open deck. `data` is the last answer for it, kept while it is reloaded. */
export interface DeckState {
  key: string;
  player: string;
  id: string;
  status: "loading" | "preparing" | "ready" | "error";
  data: DeckAnswer | null;
  progress: Progress | null;
  error: ApiError | null;
}

/** An open deck with an answer to draw. */
export type ReadyDeck = DeckState & { data: DeckAnswer };

/** One change, as the server takes it (see "Deck files" in ARCHITECTURE.md). */
export interface ChangeItem { op: "cut" | "add" | "swap"; card?: string; cut?: string; add?: string }
export type ChangeRequest = ({ op: "cut"; card: string } | { op: "add"; card: string } | { op: "swap"; cut: string; add: string }
  | { op: "group"; label: string; items: ChangeItem[] } | { op: "undo"; of: number } | { op: "settings"; settings: Settings })
  & { source?: "manual" | "suggested" };

export interface ChangeOptions {
  onDone?: (saved: boolean) => void;
  message?: string;
}

/** A change waiting for the server. */
export interface PendingEntry {
  id: number;
  deckKey: string;
  request: ChangeRequest;
  options: ChangeOptions;
  word: string;
  cards: string[];
  status: "waiting" | "sending";
  dropped: boolean;
  promise?: Promise<boolean>;
  sentRevision?: number;
}

export interface State {
  route: Route;
  player: string | null;
  wide: boolean;
  decks: decksScreen.DecksData | null;
  deck: DeckState | null;
  pending: PendingEntry[];
  lastTab: Tab;
}

/** What a screen module hands back to be drawn. */
export interface Screen {
  title: string;
  topbar: HTMLElement;
  main: HTMLElement;
}

const state: State = {
  route: { name: "decks", query: {} },
  player: readPlayer(),        // the chosen player's name, or null
  wide: WIDE.matches,          // the desktop layout (1024 px and wider)
  decks: null,                 // the Decks screen's data (decks.js)
  deck: null,                  // the open deck: {key, player, id, status, data, progress, error}
  pending: [],                 // changes waiting for the server: [{id, request, word, cards, status}]
  lastTab: "cards",            // the tab behind a sheet
};

interface View {
  scroll: number;
  id?: string;
  start?: number | null;
  end?: number | null;
  focusKey?: string;
}

let renderQueued = false;
let navigations = 0;           // address changes since the page loaded; 0 means the first address was typed, reloaded or linked to
let sheetCanGoBack = false;    // the address before the open sheet is the deck it covers, so closing the sheet can simply go back
let shown: string | null = null;              // what the main area shows, so that a sheet opening does not redraw it
let sheet: { key: string; controller: ui.Sheet; opener: HTMLElement | null } | null = null;   // the open sheet: {key, controller, opener}

/** Ask for a redraw. Several asks in the same moment make one redraw. */
function render(): void {
  if (renderQueued) return;
  renderQueued = true;
  queueMicrotask(() => {
    renderQueued = false;
    paint(false);
  });
}

function screenKey(route: Route): string {
  if (route.name === "deck") return `deck:${route.player}/${route.id}:${route.tab || state.lastTab}`;
  return route.name;
}

function captureView(): View {
  const active = document.activeElement as HTMLElement | null;
  const view: View = { scroll: window.scrollY };
  if (active && active !== document.body && (document.getElementById("main")!.contains(active) || document.getElementById("topbar")!.contains(active))) {
    if (active.id) {
      view.id = active.id;
      const input = active as HTMLInputElement;
      if (typeof input.selectionStart === "number") [view.start, view.end] = [input.selectionStart, input.selectionEnd];
    } else if (active.dataset && active.dataset.focusKey) {
      view.focusKey = active.dataset.focusKey;
    }
  }
  return view;
}

function findByKey(key: string | undefined): HTMLElement | null {
  return key ? document.querySelector<HTMLElement>(`[data-focus-key="${CSS.escape(key)}"]`) : null;
}

function restoreView(view: View, { resetScroll }: { resetScroll: boolean }): void {
  window.scrollTo(0, resetScroll ? 0 : view.scroll);
  const target = (view.id ? document.getElementById(view.id) : findByKey(view.focusKey)) as HTMLInputElement | null;
  if (target && !resetScroll) {
    target.focus({ preventScroll: true });
    if (view.start !== undefined && target.setSelectionRange) {
      try {
        target.setSelectionRange(view.start, view.end ?? null);
      } catch (e) {
        // an input type that has no selection
      }
    }
  }
}

function viewFor(route: Route): Screen {
  switch (route.name) {
    case "new": return decksScreen.newVersionView(app);
    case "new-base": return decksScreen.newBaseView(app);
    case "deck": return deckScreen.view(app);
    default: return decksScreen.decksView(app);
  }
}

/** The screen for the route, or, when drawing it throws (an answer these pages do not expect), a screen that says so. */
function drawable(route: Route): Screen {
  try {
    return viewFor(route);
  } catch (e) {
    const error = new ApiError("server", `This screen could not be drawn (${e && (e as Error).message ? (e as Error).message : e}). The server's answer may not match these pages.`);
    return { title: "Error", topbar: ui.h("div", { class: "topbar__row" }),
      main: ui.h("div", { class: "page" }, ui.failureBanner(error, { retry: () => location.reload() })) };
  }
}

/** Draw the screen from the state. `newScreen` means the person moved somewhere, so it starts at the top. */
function paint(newScreen: boolean): void {
  const route = state.route;
  const key = screenKey(route);
  const view = captureView();
  const screen = drawable(route);
  document.getElementById("topbar")!.replaceChildren(screen.topbar);
  document.getElementById("main")!.replaceChildren(screen.main);
  document.title = screen.title ? `${screen.title} · Commander decks` : "Commander decks";
  const moved = newScreen || shown !== key;
  shown = key;
  restoreView(view, { resetScroll: moved });
  if (moved && newScreen) document.getElementById("main")!.focus({ preventScroll: true });
  if (route.name === "deck") deckScreen.afterPaint(app);
}

function onRoute(): void {
  closing = null;
  const route = parseRoute(location.hash);
  const before = state.route;
  state.route = route;
  if (route.sheet && !before.sheet) sheetCanGoBack = navigations > 0;       // reached from the deck by a tap, not by a reload or a link
  if (route.name === "deck" && route.tab) state.lastTab = route.tab;
  const changedScreen = screenKey(route) !== shown;
  const changedDeck = route.name !== "deck" || before.name !== "deck" || route.player !== before.player || route.id !== before.id;
  if (changedScreen) {
    ui.dismissToast();
    ui.clearNotice();
  }
  if (route.name === "deck" && (changedDeck || !state.deck || state.deck.key !== deckKey(route.player, route.id))) loadDeck({ fresh: true });
  if (route.name === "decks") decksScreen.load(app);
  if (route.name === "new" || route.name === "new-base") decksScreen.loadForm(app);
  if (changedScreen || changedDeck) paint(changedDeck || before.name !== route.name);
  syncSheet();
}

// -------------------------------------------------------------------------------------------------------------- sheets

let closing: string | null = null;             // the sheet address a close was already asked for (cleared on the next address change)

function closeSheet(): void {
  const route = state.route;
  if (route.name !== "deck" || !route.sheet) return;
  if (closing === location.hash) return;                                  // a double tap: going back twice would leave the deck
  closing = location.hash;
  if (sheetCanGoBack) history.back();                                     // the address before it was the deck
  else location.replace(link.deck(route.player, route.id, state.lastTab));  // reached by a reload or a link: there is nothing to go back to
}

function syncSheet(): void {
  const route = state.route;
  const wanted = route.name === "deck" && route.sheet
    ? `${route.player}/${route.id}/${route.sheet.kind}/${route.sheet.name || ""}/${route.sheet.cut || ""}/${route.sheet.card || ""}` : null;
  if (sheet && sheet.key !== wanted) {
    const opener = sheet.opener;
    sheet.controller.destroy({ restoreFocus: wanted === null });
    sheet = null;
    if (wanted !== null) pendingOpener = opener;                       // sheet to sheet: the first one's opener is where focus returns
  }
  if (wanted && !sheet && route.name === "deck" && route.sheet) {
    const tapped = lastTapped && lastTapped.isConnected ? lastTapped : null;
    const opener = pendingOpener || tapped || (document.activeElement as HTMLElement | null);
    pendingOpener = null;
    lastTapped = null;
    const focusKey = opener && opener.dataset ? opener.dataset.focusKey : "";
    const returnFocus = () => findByKey(focusKey) || (opener && opener.isConnected ? opener : document.getElementById("main"));
    const options = { returnFocus, onDismiss: closeSheet };
    const controller = route.sheet.kind === "card"
      ? cardSheet.open(app, route.sheet.name, options)
      : addSheet.open(app, route.sheet, options);
    sheet = { key: wanted, controller, opener };
  }
}
let pendingOpener: HTMLElement | null = null;
let lastTapped: HTMLElement | null = null;         // the link or button last clicked: where focus goes back to when its sheet closes (Safari does not focus a clicked link)
document.addEventListener("click", (e) => {
  lastTapped = e.target instanceof Element ? e.target.closest<HTMLElement>("a, button") : null;
}, true);

// ------------------------------------------------------------------------------------------------------- the open deck

/**
 * Load the deck the route names. A first open can take several seconds while the server downloads the commander's data;
 * it answers 202 with how far it has got, and this asks again every second until the deck is ready.
 */
async function loadDeck({ fresh = false } = {}): Promise<void> {
  const route = state.route;
  if (route.name !== "deck") return;
  const key = deckKey(route.player, route.id);
  const keep = !fresh && state.deck && state.deck.key === key ? state.deck.data : null;
  const token = ++deckToken;
  const deck: DeckState = { key, player: route.player, id: route.id, status: "loading", data: keep, progress: null, error: null };
  state.deck = deck;
  render();
  try {
    const answer = await callReady<DeckAnswer>("GET", deckPath(route.player, route.id), undefined, {
      onProgress: (progress) => {
        if (token !== deckToken) return;
        deck.status = "preparing";
        deck.progress = progress;
        render();
      },
      keepGoing: () => token === deckToken,
    });
    if (token !== deckToken || answer.status === 202) return;
    acceptDeck(answer.body);
  } catch (e) {
    if (token !== deckToken) return;
    deck.status = "error";
    deck.error = e as ApiError;
    render();
  }
}
let deckToken = 0;

/** Why a deck answer cannot be drawn (a part every screen reads is missing), or null. */
function missingPart(body: any): string | null {
  if (!body || typeof body !== "object") return "everything";
  for (const key of ["version", "base", "spec", "commanders", "cards", "diff", "metrics", "sources"]) {
    if (body[key] === undefined || body[key] === null) return `"${key}"`;
  }
  if (!body.metrics.headline || !Array.isArray(body.metrics.groups)) return '"metrics"';
  return null;
}

function acceptDeck(body: DeckAnswer): void {
  if (!state.deck) return;
  const missing = missingPart(body);
  if (missing) {
    state.deck.status = "error";
    state.deck.error = new ApiError("server", `The server's answer for this deck is missing ${missing}, so it cannot be shown.`);
    render();
    return;
  }
  state.deck.data = body;
  state.deck.status = "ready";
  state.deck.progress = null;
  state.deck.error = null;
  render();
}

// ------------------------------------------------------------------------------------------------------ saving changes
// One change at a time for each deck. A tap adds a request to the queue and dims its card; nothing on screen moves until
// the server answers, and then everything is redrawn from the answer. If one request fails, the ones queued behind it are
// not sent (they were made for a deck that is not what the person thought it was); the notice offers to send them all again.

let entrySeq = 0;
const queues = new Map<string, Promise<boolean>>();      // deck key -> the end of that deck's queue

const WORDS: Record<string, string> = { cut: "Cutting…", add: "Adding…", swap: "Swapping…", undo: "Undoing…", group: "Applying…", settings: "Saving…" };

function cardsOf(request: ChangeRequest): string[] {
  if (request.op === "cut" || request.op === "add") return [request.card];
  if (request.op === "swap") return [request.cut];
  if (request.op === "group") return request.items.map((item) => (item.op === "add" ? item.add || item.card : item.cut || item.card)).filter((name): name is string => Boolean(name));
  return [];
}

function describe(request: ChangeRequest): string {
  switch (request.op) {
    case "cut": return `cut of ${request.card}`;
    case "add": return `adding ${request.card}`;
    case "swap": return `swap of ${request.cut} for ${request.add}`;
    case "group": return `"${request.label}"`;
    case "undo": return `undo of change ${request.of}`;
    default: return request.settings ? "new settings" : "change";
  }
}

/**
 * Save one change: {op: "cut", card}, {op: "add", card}, {op: "swap", cut, add}, {op: "group", label, items},
 * {op: "undo", of} or {op: "settings", settings}. `source` ("manual" or "suggested") rides along. Options: `onDone(saved)`
 * is called when it has finished, and `message` replaces the server's words in the toast. Resolves to true when it was
 * saved (or answered "nothing to do") and false when it failed.
 */
function change(request: ChangeRequest, options: ChangeOptions = {}): Promise<boolean> {
  const deck = state.deck;
  if (!deck || deck.status !== "ready") return Promise.resolve(false);
  const same = JSON.stringify(request);
  const twin = state.pending.find((e) => e.deckKey === deck.key && JSON.stringify(e.request) === same);
  if (twin && twin.promise) return twin.promise;                          // a double tap: one change, not two
  ui.clearNotice();
  const entry: PendingEntry = { id: ++entrySeq, deckKey: deck.key, request, options, word: WORDS[request.op] || "Saving…", cards: cardsOf(request), status: "waiting", dropped: false };
  state.pending.push(entry);
  render();
  const tail = (queues.get(deck.key) || Promise.resolve(true)).then(() => sendChange(deck.key, entry));
  entry.promise = tail;
  queues.set(deck.key, tail.catch(() => false));
  return tail;
}

function leaveQueue(entry: PendingEntry): void {
  state.pending = state.pending.filter((e) => e !== entry);
}

async function sendChange(key: string, entry: PendingEntry): Promise<boolean> {
  if (entry.dropped) return false;
  entry.status = "sending";
  const stillOpen = () => Boolean(state.deck) && state.deck!.key === key;       // the person may have gone to another deck meanwhile
  try {
    for (let attempt = 0; ; attempt++) {
      const deck = state.deck;
      if (!deck || deck.key !== key || !deck.data) throw new ApiError("not_found", "That deck is no longer open.");
      const revision = deck.data.version.revision;
      entry.sentRevision = revision;
      const path = deckPath(deck.player, deck.id);
      const request = entry.request;
      const answer = request.op === "settings"
        ? await call<DeckAnswer>("PATCH", path, { revision, settings: request.settings })
        : await call<DeckAnswer>("POST", `${path}/changes`, { revision, ...request });
      if (answer.status === 202) {
        // The server has no prepared copy of this deck (it was restarted). A change answered 202 was not made, so wait
        // for the numbers and send it again; a settings change answered 202 is saved, and the numbers are on their way.
        const ready = await callReady<DeckAnswer>("GET", path, undefined, { onProgress: (progress) => { if (stillOpen()) state.deck!.progress = progress; } });
        if (stillOpen()) acceptDeck(ready.body);
        if (request.op === "settings") {
          finishChange(entry, { changed: true, message: "Saved" }, ready.body, stillOpen());
          return true;
        }
        if (attempt >= 2) throw new ApiError("server", "The server kept saying it was still getting the deck ready.");
        continue;
      }
      if (stillOpen()) acceptDeck(answer.body);
      finishChange(entry, answer.body.result || { changed: true, message: "Saved" }, answer.body, stillOpen());
      return true;
    }
  } catch (e) {
    await failChange(key, entry, e instanceof ApiError ? e : new ApiError("server", String(e && (e as Error).message || e)));
    return false;
  }
}

/** The change is saved: leave the queue, tell the person, and offer Undo for what can be undone (while that deck is still open). */
function finishChange(entry: PendingEntry, result: { changed: boolean; message?: string }, body: DeckAnswer, open: boolean): void {
  leaveQueue(entry);
  const message = String((result.changed && entry.options.message) || result.message || "Saved").replace(/\.$/, "");
  const changes = body.version.changes || [];
  const last = changes[changes.length - 1];
  const undoable = open && result.changed && entry.request.op !== "undo" && entry.request.op !== "settings" && last && Number.isInteger(last.n);
  ui.toast(message, undoable ? { action: { label: "Undo", onClick: () => change({ op: "undo", of: last.n }) } } : {});
  if (entry.options.onDone) entry.options.onDone(true);
  render();
}

/** The change failed: put the card back, say why, and keep what was not sent so that Retry can send it. */
async function failChange(key: string, entry: PendingEntry, error: ApiError): Promise<void> {
  const failed = [entry];
  for (const other of state.pending.filter((e) => e !== entry && e.status === "waiting")) {
    other.dropped = true;
    failed.push(other);
  }
  state.pending = state.pending.filter((e) => !failed.includes(e));
  if (error.kind === "conflict") await loadDeckQuietly(key);
  render();
  postFailure(error, failed);
  for (const e of failed) if (e.options.onDone) e.options.onDone(false);
}

async function loadDeckQuietly(key: string | null): Promise<void> {
  const deck = state.deck;
  if (!deck || deck.key !== key) return;
  try {
    const answer = await callReady<DeckAnswer>("GET", deckPath(deck.player, deck.id));
    if (state.deck && state.deck.key === key && answer.status === 200) acceptDeck(answer.body);
  } catch (e) {
    // the notice will say the server could not be reached; the old copy stays on screen meanwhile
  }
}

/** "Your cut of X wasn't saved." or, when the server went quiet and may have saved it, "... may not have been saved." */
function failedText(failed: PendingEntry[], { unsure = false } = {}): string {
  const [first, ...rest] = failed;
  const what = `${describe(first.request)}${rest.length ? ` and ${rest.length} more ${rest.length === 1 ? "change" : "changes"}` : ""}`;
  if (unsure) return `Your ${what} may not have been saved.`;
  return `Your ${what} ${rest.length ? "weren't" : "wasn't"} saved.`;
}

function postFailure(error: ApiError, failed: PendingEntry[]): void {
  const key = state.deck && state.deck.key;
  const dismiss = { label: "Dismiss", onClick: () => ui.clearNotice() };
  const sendAgain = () => {
    ui.clearNotice();
    for (const entry of failed) change(entry.request, entry.options);
  };
  const again = (label: string) => ({ label, kind: "primary" as const, onClick: sendAgain });
  // After a timeout the change may have been saved anyway (the server did the work, then was slow to answer). So Retry
  // first reads the deck again: if its revision has moved on, the change is not sent a second time.
  const checkThenSendAgain = async () => {
    ui.clearNotice();
    const sent = failed[0].sentRevision;
    await loadDeckQuietly(key);
    const now = state.deck && state.deck.key === key && state.deck.data ? state.deck.data.version.revision : sent;
    if (sent !== undefined && now !== undefined && now > sent) {
      ui.toast("The deck changed while the server was slow, so it was reloaded and nothing was sent again. The Changes tab shows what is saved.", { duration: 12000 });
      return;
    }
    for (const entry of failed) change(entry.request, entry.options);
  };
  let notice;
  if (error.cannotReach) {
    const unsure = error.kind === "timeout";
    notice = ui.failureBanner(error, { retry: unsure ? checkThenSendAgain : sendAgain, note: failedText(failed, { unsure }), actions: [dismiss] });
  } else if (error.kind === "conflict") {
    notice = ui.banner({
      tone: "warn", title: "This deck changed on another device,",
      text: `so it was reloaded. ${failedText(failed)}`, actions: [again("Try again"), dismiss],
    });
  } else if (error.kind === "invalid" || error.kind === "not_found") {
    notice = ui.banner({ tone: "bad", title: "Not saved.", text: error.message, actions: [dismiss] });
  } else {
    notice = ui.failureBanner(error, { retry: sendAgain, actions: [dismiss] });
  }
  ui.postNotice(notice);
}

// ------------------------------------------------------------------------------------------------------------ the app

const app = {
  state,
  link,
  render,
  go: (hash: string) => { location.hash = hash; },
  replace: (hash: string) => { location.replace(hash); },
  closeSheet,
  loadDeck,
  change,
  undo: (n: number) => change({ op: "undo", of: n }),
  /** The word to lay over a card whose change is waiting ("Cutting…"), or "". */
  pendingWord(name: string): string {
    const entry = state.pending.find((e) => e.cards.includes(name));
    return entry ? entry.word : "";
  },
  get saving(): boolean {
    return state.pending.length > 0;
  },
  /** Remember who is playing on this device (no reload). */
  rememberPlayer(name: string): void {
    state.player = name;
    writePlayer(name);
  },
  /** Switch to another player and show their decks. */
  setPlayer(name: string): void {
    app.rememberPlayer(name);
    state.decks = null;
    decksScreen.load(app);
  },
};

/** What every screen module is handed: the state, the links, and the ways to change things. */
export type App = typeof app;

WIDE.addEventListener("change", () => {
  state.wide = WIDE.matches;
  render();
});

window.addEventListener("hashchange", () => {
  navigations += 1;
  onRoute();
});

document.addEventListener("keydown", (e) => {
  // "/" jumps to the search box of the Cards tab, as on the card-reference site
  const target = e.target as HTMLElement | null;
  const typing = target && /^(input|textarea|select)$/i.test(target.tagName);
  if (e.key === "/" && !typing && !ui.sheetIsOpen()) {
    const box = document.getElementById("deck-search") as HTMLInputElement | null;
    if (box) {
      e.preventDefault();
      box.focus();
      box.select();
    }
  }
});

onRoute();
