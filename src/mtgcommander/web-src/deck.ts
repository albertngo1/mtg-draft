// The Deck screen: the header, the stat line, the four tabs (Cards, Metrics, Changes, Suggestions) and the banners that
// describe the deck itself. Every number on it comes from the server's answer (api.js); this file sorts, folds and formats.

import { call, callReady, deckPath } from "./api.js";
import type { ApiError } from "./api.js";
import * as ui from "./ui.js";
import * as metrics from "./metrics.js";
import type { App, DeckState, ReadyDeck, Screen, Tab } from "./app.js";
import type { CardFace, DeckAnswer, DeckCard, LoggedChange, PricePoint, Progress, StatusAnswer, SuggestAnswer, Swap } from "./types.js";

const { h } = ui;

// ---------------------------------------------------------------------------------------------------- the Cards tab

// The server's sections are the card types; the pages fold them into four, as the printed lists do.
const SECTION_FOLD: Record<string, string> = {
  Creatures: "Creatures", Instants: "Instants & sorceries", Sorceries: "Instants & sorceries",
  Planeswalkers: "Other permanents", Artifacts: "Other permanents", Enchantments: "Other permanents",
  Battles: "Other permanents", Other: "Other permanents", Lands: "Lands",
};
const SECTION_ORDER = ["Creatures", "Instants & sorceries", "Other permanents", "Lands"];
const SECTION_NOUN: Record<string, string> = { "Creatures": " creatures", "Instants & sorceries": " instants and sorceries", "Other permanents": "", "Lands": " lands" };
const PREVIEW = 9;                       // tiles a section shows before "Show N more" (three rows on a phone)
const ROLE_CHIPS = [["ramp", "Ramp"], ["draw", "Draw"], ["removal", "Removal"], ["wipe", "Wipes"], ["counter", "Counters"],
  ["protection", "Protection"], ["recursion", "Recursion"], ["tutor", "Tutors"], ["finisher", "Finishers"]];

interface CardsState {
  deckKey: string | null;
  filter: string;
  query: string;
  expanded: Set<string>;
  redraw: (() => void) | null;
}

// What the Cards tab remembers while the deck is open: the filter, the search text, and which sections are unfolded.
const cards: CardsState = { deckKey: null, filter: "all", query: "", expanded: new Set(), redraw: null };

function cardsState(deck: DeckState): CardsState {
  if (cards.deckKey !== deck.key) Object.assign(cards, { deckKey: deck.key, filter: "all", query: "", expanded: new Set(), redraw: null });
  return cards;
}

const copiesIn = (list: DeckCard[]) => list.reduce((n, card) => n + card.count, 0);

function searchTerms(text: string): string[] {
  return text.toLowerCase().split(/\s+/).filter(Boolean);
}

function cardsTab(app: App, deck: ReadyDeck): HTMLDivElement {
  const data = deck.data;
  const st = cardsState(deck);
  const chipsBox = h("div", { class: "chips", role: "group", "aria-label": "Filter the cards" });
  const area = h("div", { class: "cardsarea" });

  const keeps = (card: DeckCard) => {
    if (st.filter === "new" && !card.new) return false;
    if (st.filter.startsWith("role:") && !card.roles.includes(st.filter.slice(5))) return false;
    const terms = searchTerms(st.query);
    const haystack = `${card.name} ${card.type}`.toLowerCase();
    return terms.every((term) => haystack.includes(term));
  };

  const chipFor = (label: string, count: number, value: string) => ui.chip({
    label, count, pressed: st.filter === value,
    onClick: () => { st.filter = st.filter === value && value !== "all" ? "all" : value; draw(); },
  });

  const draw = () => {
    const list = data.cards;
    const chips = [chipFor("All", copiesIn(list), "all")];
    const fresh = list.filter((card) => card.new);
    if (fresh.length) chips.push(chipFor("New", copiesIn(fresh), "new"));
    const known = new Set(ROLE_CHIPS.map(([role]) => role));
    const roleList = ROLE_CHIPS.concat([...new Set(list.flatMap((card) => card.roles))].filter((r) => !known.has(r)).map((r) => [r, ui.capitalize(r)]));
    for (const [role, label] of roleList) {
      const withRole = list.filter((card) => card.roles.includes(role));
      if (withRole.length) chips.push(chipFor(label, copiesIn(withRole), `role:${role}`));
    }
    chipsBox.replaceChildren(...chips);
    area.replaceChildren(...sections(app, deck, st, keeps));
  };
  st.redraw = draw;
  draw();

  const parts = [chipsBox];
  if (!app.state.wide) parts.push(deckSearch(st).el);
  return h("div", {}, parts, area);
}

function deckSearch(st: CardsState): { input: HTMLInputElement; el: HTMLDivElement } {
  const box = ui.searchBox({
    id: "deck-search", label: "Search this deck", placeholder: "Search this deck", value: st.query,
    onInput: (value) => { st.query = value; if (st.redraw) st.redraw(); },
  });
  box.input.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && st.query) {
      e.preventDefault();
      st.query = "";
      box.input.value = "";
      if (st.redraw) st.redraw();
    }
  });
  return box;
}

function sections(app: App, deck: ReadyDeck, st: CardsState, keeps: (card: DeckCard) => boolean): HTMLElement[] {
  const { player, id } = deck;
  const groups = new Map<string, DeckCard[]>(SECTION_ORDER.map((name) => [name, []]));
  for (const card of deck.data.cards.filter(keeps)) {
    const name = SECTION_FOLD[card.section] || "Other permanents";
    groups.get(name)!.push(card);
  }
  const out: HTMLElement[] = [];
  for (const [name, list] of groups) {
    if (!list.length) continue;
    const capped = !st.query && st.filter === "all" && !st.expanded.has(name) && list.length > PREVIEW;
    const shown = capped ? list.slice(0, PREVIEW) : list;
    out.push(ui.sectionLabel(`${name} · ${copiesIn(list)}`));
    out.push(h("div", { class: "grid" }, shown.map((card) => ui.cardTile(card, {
      href: app.link.card(player, id, card.name), focusKey: `card:${card.name}`, count: card.count,
      badge: card.new ? (card.owned ? "NEW · OWNED" : "NEW") : "", pending: app.pendingWord(card.name),
    }))));
    if (capped) {
      out.push(h("button", {
        type: "button", class: "more",
        onclick: () => { st.expanded.add(name); st.redraw!(); },
      }, `Show ${list.length - PREVIEW} more${SECTION_NOUN[name]}`));
    }
  }
  if (!out.length) {
    out.push(ui.emptyState({
      title: "No card matches", text: st.query ? `Nothing in this deck matches “${st.query}”.` : "Nothing in this deck has that role.",
      action: ui.button({ label: "Show every card", kind: "outline", onClick: () => { st.query = ""; st.filter = "all"; const box = document.getElementById("deck-search") as HTMLInputElement | null; if (box) box.value = ""; st.redraw!(); } }),
    }));
  }
  return out;
}

/** How many cards were added and cut against the base deck, as the server counted them (the "changes" group). */
function changeCounts(data: DeckAnswer): { added: number | null; cut: number | null } {
  const added = metrics.findItem(data.metrics, "changes_added");
  const cut = metrics.findItem(data.metrics, "changes_cut");
  return { added: added ? added.value : null, cut: cut ? cut.value : null };
}

const swapWord = (n: number | null) => `${n} ${n === 1 ? "swap" : "swaps"}`;

/** "36 swaps since Squirreled Away": as many cards cut as added is a swap each; otherwise say how many of each. */
function summaryTitle({ added, cut }: { added: number | null; cut: number | null }, baseName: string): string {
  if (!added && !cut) return `No changes since ${baseName}`;
  if (added === cut) return `${swapWord(added)} since ${baseName}`;
  return `${added || 0} added and ${cut || 0} cut since ${baseName}`;
}

// ------------------------------------------------------------------------------------------------- the Changes tab

const changesUi: { showAllMoved: boolean; root: string | null } = { showAllMoved: false, root: null };

/** The folder the deck files are in, asked of the server once (it is only a line of text at the bottom of the tab). */
function loadRoot(app: App): void {
  if (changesUi.root !== null) return;
  changesUi.root = "";
  call<StatusAnswer>("GET", "/api/status").then((answer) => {
    changesUi.root = answer.body.settings.decks || "";
    app.render();
  }).catch(() => {});
}

const SHOWN_THUMBS = 6;
const SHOWN_NAMES = 10;

/** Thumbnails of the first few cards, then the rest of their names in a sentence: "and Cultivate, Forest ... and 20 more." */
function cardStrip(app: App, deck: ReadyDeck, list: { card: CardFace; copies: number }[], { cut = false } = {}): HTMLElement[] {
  const [first, rest] = [list.slice(0, SHOWN_THUMBS), list.slice(SHOWN_THUMBS)];
  const out: HTMLElement[] = [h("div", { class: "thumbs" }, first.map(({ card, copies }) => ui.cardTile(card, {
    size: "mini", href: app.link.card(deck.player, deck.id, card.name), count: copies, cut, focusKey: `card:${card.name}`,
  })))];
  if (rest.length) {
    const named = rest.slice(0, SHOWN_NAMES).map(({ card, copies }) => (copies > 1 ? `${copies} ${card.name}` : card.name));
    const more = rest.length - named.length;
    out.push(h("p", { class: "para muted small", text: `and ${named.join(", ")}${more > 0 ? ` and ${more} more` : ""}.` }));
  }
  return out;
}

function changeTitle(change: LoggedChange): string {
  switch (change.op) {
    case "add": return `Added ${change.add}`;
    case "cut": return `Cut ${change.cut}`;
    case "swap": return `Swapped ${change.cut} for ${change.add}`;
    case "group": return `Applied “${change.label}”`;
    case "undo": return `Undid change ${change.of}`;
    default: return `Change ${change.n}`;
  }
}

function changeNote(change: LoggedChange, player: string): string {
  const bits: string[] = [];
  if (change.op === "group") {
    const items = change.items || [];
    bits.push(`${items.length} ${items.every((item) => item.op === "swap") ? (items.length === 1 ? "swap" : "swaps") : (items.length === 1 ? "change" : "changes")}`);
  }
  if (change.source === "suggested") bits.push("suggested by the tool");
  else if (change.source === "manual") bits.push("picked by hand");
  bits.push(player, ui.when(change.at));
  return bits.join(" · ");
}

function changesTab(app: App, deck: ReadyDeck): HTMLDivElement {
  const data = deck.data;
  loadRoot(app);
  const byName = new Map<string, CardFace>([...data.cards, ...data.cut_cards].map((card) => [card.name, card]));
  const strip = (pairs: [number, string][]) => pairs.map(([copies, name]) => ({ card: byName.get(name) || { name, image: "", cost: "", type: "" }, copies })).filter((entry) => entry.card);
  const counts = changeCounts(data);
  const net = metrics.findItem(data.metrics, "changes_net_cost");
  const out = h("div", { class: app.saving ? "stack is-faded" : "stack" });

  out.append(h("section", { class: "summary" },
    h("div", { class: "summary__title", text: summaryTitle(counts, data.base.name) }),
    net && ui.isNumber(net.value) ? h("div", { class: "summary__sub", text: `${ui.money(net.value)} net cost of the changes` }) : null,
    ...(net ? net.why.map((line) => h("p", { class: "para muted small", text: line })) : [])));

  const moved = [];
  for (const group of data.metrics.groups) {
    if (group.id === "changes") continue;
    for (const item of group.items) {
      if (ui.hasMoved(item)) moved.push(item);
    }
  }
  if (moved.length) {
    const shown = changesUi.showAllMoved ? moved : moved.slice(0, 9);
    out.append(h("section", {}, ui.sectionLabel("Before → after", { tight: true }),
      shown.map((item) => h("div", { class: "tr" }, h("span", { text: item.label }),
        h("span", { class: "tr__v" }, `${ui.valueText(item.base, item.unit)} → `,
          h("b", { class: item.status === "short" ? "is-short" : item.status === "over" ? "is-over" : null, text: ui.valueText(item.value, item.unit) }),
          h("span", { class: "tr__change", text: ` (${ui.signedValue(item.change, item.unit)})` })))),
      moved.length > 9 ? ui.button({
        label: changesUi.showAllMoved ? "Show fewer" : `Show all ${moved.length} numbers that changed`, kind: "quiet", size: "small",
        onClick: () => { changesUi.showAllMoved = !changesUi.showAllMoved; app.render(); },
      }) : null,
      ui.button({ label: "Every metric, before and after", kind: "quiet", size: "small", href: app.link.deck(deck.player, deck.id, "metrics") })));
  }

  if (data.diff.added.length) {
    out.append(h("section", {}, ui.sectionLabel(`Added · ${counts.added}`, { tight: true }), cardStrip(app, deck, strip(data.diff.added))));
  }
  if (data.diff.cut.length) {
    out.append(h("section", {}, ui.sectionLabel(`Cut · ${counts.cut}`, { tight: true }), cardStrip(app, deck, strip(data.diff.cut), { cut: true })));
  }

  const history = h("div", { class: "stack" });
  const settings = data.version.settings;
  for (const change of [...(data.version.changes || [])].reverse()) {
    const undoing = app.state.pending.some((entry) => entry.request.op === "undo" && entry.request.of === change.n);
    const canUndo = change.op !== "undo" && !change.undone;
    history.append(h("div", { class: change.undone ? "history is-undone" : "history" },
      h("div", { class: "history__main" },
        h("div", { class: "history__title", text: changeTitle(change) }),
        h("div", { class: "history__sub", text: change.undone ? `undone · ${changeNote(change, deck.player)}` : changeNote(change, deck.player) })),
      canUndo ? ui.button({
        label: "Undo", kind: "outline", size: "small", busy: undoing, disabled: app.saving && !undoing, ariaLabel: `Undo change ${change.n}: ${changeTitle(change)}`,
        onClick: () => app.undo(change.n),
      }) : null));
  }
  const words = ([] as string[]).concat(data.spec.themes || [], data.spec.playstyle ? [data.spec.playstyle] : []);
  history.append(h("div", { class: "history" }, h("div", { class: "history__main" },
    h("div", { class: "history__title", text: `Created from ${data.base.name}` }),
    h("div", { class: "history__sub", text: [data.spec.bracket ? `Bracket ${data.spec.bracket}` : "", settings.budget !== undefined && settings.budget !== null ? `budget ${ui.dollars(settings.budget)}` : "",
      words.join(", "), deck.player, ui.when(data.version.created)].filter(Boolean).join(" · ") }))));
  out.append(h("section", {}, ui.sectionLabel("History", { tight: true }), history,
    changesUi.root ? h("p", { class: "footnote", style: { marginTop: "12px" }, text: `Saved in ${ui.pathTail(changesUi.root)}/${deck.player}/${deck.id}.json` }) : null));
  return out;
}

// -------------------------------------------------------------------------------------------- the Suggestions tab
// The suggestions are asked for again after every change: a price point worked out before a change is never applied,
// because the swaps in it may no longer fit the list.

interface SuggestState {
  key: string | null;
  status: "idle" | "running" | "ready" | "error";
  revision: number | null;
  budget: number | null;
  result: SuggestAnswer | null;
  error: ApiError | null;
  progress: Progress | null;
  token: number;
  selected: number;
  editing: boolean;
  showAll: boolean;
}

const suggest: SuggestState = { key: null, status: "idle", revision: null, budget: null, result: null, error: null, progress: null, token: 0, selected: 0, editing: false, showAll: false };
const SHOWN_SWAPS = 6;

function resetSuggestions(key: string): void {
  suggest.token += 1;
  Object.assign(suggest, { key, status: "idle", revision: null, budget: null, result: null, error: null, progress: null, selected: 0, editing: false, showAll: false });
}

/** Runs after each draw of the deck screen: asks for suggestions when the Suggestions tab is showing and has none for this list. */
export function afterPaint(app: App): void {
  const { state } = app;
  const deck = state.deck;
  if (!deck || deck.status !== "ready" || !deck.data) return;
  if (state.route.name !== "deck" || (state.route.tab || state.lastTab) !== "suggestions") return;
  if (suggest.key !== deck.key) resetSuggestions(deck.key);
  const { budget } = deck.data.version.settings;
  const { revision } = deck.data.version;
  if (budget === undefined || budget === null) return;
  if (suggest.revision === revision && suggest.budget === budget && suggest.status !== "idle") return;
  askForSuggestions(app, deck as ReadyDeck, budget, revision);
}

async function askForSuggestions(app: App, deck: ReadyDeck, budget: number, revision: number): Promise<void> {
  const token = ++suggest.token;
  Object.assign(suggest, { status: "running", revision, budget, result: null, error: null, progress: null, selected: 0, showAll: false });
  app.render();
  try {
    const answer = await callReady<SuggestAnswer>("POST", `${deckPath(deck.player, deck.id)}/suggest`, { budget }, {
      onProgress: (progress) => { if (token === suggest.token) { suggest.progress = progress; app.render(); } },
      keepGoing: () => token === suggest.token,
    });
    if (token !== suggest.token || answer.status === 202) return;
    suggest.result = answer.body;
    suggest.revision = answer.body.revision;           // the revision the swaps were worked out for
    suggest.status = "ready";
  } catch (e) {
    if (token !== suggest.token) return;
    suggest.status = "error";
    suggest.error = e as ApiError;
  }
  app.render();
}

function budgetForm(app: App, current: number | null): HTMLDivElement {
  const input = h("input", { id: "budget", class: "input", type: "number", min: "0", step: "any", inputmode: "decimal", value: current === null ? "" : String(current), placeholder: "For example 100" });
  const error = h("div", { class: "field__error", role: "alert" });
  const save = () => {
    const text = input.value.trim();
    const value = Number(text);
    if (!text || !Number.isFinite(value) || value < 0) {
      error.textContent = "Type an amount in dollars: zero or more.";
      return;
    }
    suggest.editing = false;
    app.change({ op: "settings", settings: { budget: value } }, { message: `Budget set to ${ui.dollars(value)}` });
  };
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); save(); } });
  return h("div", { class: "field" },
    h("label", { class: "field__label", for: "budget", text: "Budget in dollars" }),
    h("div", { class: "btnrow" }, h("div", { style: { flex: "1", minWidth: "140px" } }, input),
      ui.button({ label: current === null ? "Find swaps" : "Save", kind: "primary", onClick: save }),
      current === null ? null : ui.button({ label: "Cancel", kind: "outline", onClick: () => { suggest.editing = false; app.render(); } })),
    h("div", { class: "field__hint", text: "Suggestions swap cards for ones that fit the deck better, and stay inside this much money. Cards you own cost nothing." }),
    error);
}

/** "spent $185.43 · $14.57 left" or "spent $352.10 · over by $152.10", from the server's numbers for the list as it is now
 * (nothing until its answer for this revision has come). The page subtracts nothing: `over` and `left` are the server's. */
function spentWords(revision: number): string {
  const result = suggest.status === "ready" ? suggest.result : null;
  if (!result || result.revision !== revision || !ui.isNumber(result.spent)) return "";
  return `spent ${ui.money(result.spent)} · ${(result.over ?? 0) > 0 ? `over by ${ui.money(result.over)}` : `${ui.money(result.left)} left`}`;
}

function suggestionsTab(app: App, deck: ReadyDeck): HTMLDivElement {
  const data = deck.data;
  if (suggest.key !== deck.key) resetSuggestions(deck.key);
  const settings = data.version.settings;
  const budget = settings.budget === undefined ? null : settings.budget;
  const wrap = h("div", { class: "stack" });
  if (budget === null) {
    wrap.append(budgetForm(app, null));
    return wrap;
  }
  const words = ([] as string[]).concat(data.spec.themes || [], data.spec.playstyle ? [data.spec.playstyle] : []);
  const owned = (settings.owned_precons || []).length;
  wrap.append(h("div", { class: "btnrow", style: { alignItems: "center" } },
    h("span", { class: "footnote", style: { flex: "1" }, text: [`Budget ${ui.dollars(budget)}`, spentWords(data.version.revision), `Bracket ${data.spec.bracket}`, words.join(", "), owned ? `you own ${owned} other ${owned === 1 ? "deck" : "decks"}` : ""].filter(Boolean).join(" · ") }),
    ui.button({ label: "Change", kind: "quiet", size: "small", onClick: () => { suggest.editing = !suggest.editing; app.render(); } })));
  if (suggest.editing) wrap.append(budgetForm(app, budget));
  if (suggest.status === "error") {
    wrap.append(ui.failureBanner(suggest.error!, { retry: () => { suggest.status = "idle"; suggest.revision = null; app.render(); } }));
  } else if (suggest.status !== "ready") {
    wrap.append(ui.working(suggest.progress && suggest.progress.message ? suggest.progress.message : "Finding swaps…"));
  } else {
    wrap.append(...suggestionResult(app, deck, suggest.result!));
  }
  return wrap;
}

/** A price point is money still to spend on top of what the version has spent: "Up to $14.57 more". Once the budget is
 *  used up the search has $0, so its one point holds only swaps with cards the player already owns, and says so. */
const upTo = (point: PricePoint) => (point.budget > 0 ? `Up to ${ui.dollars(point.budget)} more` : "With cards you own");

/** Why no swap is offered: none beats the list within what is left, or, with the budget used up, the money is the limit. */
function nothingToSuggestText(result: SuggestAnswer): string {
  if (result.left !== 0) return `No swap beats the current list within ${ui.dollars(result.left)} more.`;
  const sofar = ui.isNumber(result.spent) ? ` (${ui.money(result.spent)} so far)` : "";
  return `This version has spent its ${ui.dollars(result.budget)} budget${sofar}. With nothing left to spend, a suggestion can only bring in a card from a precon you own that the deck is not using, and none of those beats the current list. Raise the budget, or cut cards you bought to free money.`;
}

/** "Suggestions keep your changes: the 32 cards you added stay, and the 32 you cut are not offered again. Undo a change to
 *  reconsider it." The counts are the server's (`changes_kept`); there is no line while the player has made no change. */
function keepsLine({ added = 0, cut = 0 }: { added?: number; cut?: number } = {}): HTMLParagraphElement | null {
  const cards = (n: number) => `${n} ${n === 1 ? "card" : "cards"}`;
  const parts: string[] = [];
  if (added) parts.push(`the ${cards(added)} you added ${added === 1 ? "stays" : "stay"}`);
  if (cut) parts.push(`the ${added ? cut : cards(cut)} you cut ${cut === 1 ? "is" : "are"} not offered again`);
  return parts.length ? h("p", { class: "muted small", text: `Suggestions keep your changes: ${parts.join(", and ")}. Undo a change to reconsider it.` }) : null;
}

function suggestionResult(app: App, deck: ReadyDeck, result: SuggestAnswer): HTMLElement[] {
  const out: HTMLElement[] = [];
  const locked = result.revision !== deck.data.version.revision || app.saving;   // never apply swaps worked out before a change
  const swaps = result.swaps;
  const keeps = keepsLine(result.changes_kept);
  if (keeps) out.push(keeps);
  if (!swaps.length) {
    out.push(ui.emptyState({ title: "Nothing to suggest", text: nothingToSuggestText(result) }));
    if (result.cheap_adds.length) {
      out.push(h("section", {}, ui.sectionLabel("The cheapest cards that would help", { tight: true }),
        result.cheap_adds.map((add) => h("p", { class: "para" }, h("b", { text: add.card }), ` costs ${ui.money(add.price)} and would add ${ui.signed(add.gain)} to the deck score, more than the budget allows.`))));
    }
  } else {
    const points = result.price_points;
    const chosen = Math.min(suggest.selected, points.length - 1);
    out.push(h("section", { class: "stack" }, ui.sectionLabel("Price points", { tight: true }),
      points.map((point, i) => {
        const title = upTo(point);
        const row = h("div", { class: i === points.length - 1 ? "pp pp--budget" : "pp" },
          h("button", {
            type: "button", class: "pp__pick", "aria-pressed": i === chosen, onclick: () => { suggest.selected = i; suggest.showAll = false; app.render(); },
          }, h("span", { class: "pp__title", text: title }),
          h("span", { class: "pp__meta" }, "spend ", h("b", { text: ui.money(point.spent) }),
            ` · score ${ui.oneDecimal(result.value_before)} → ${ui.oneDecimal(point.value)}`,
            ui.isNumber(point.change) ? ` (${ui.signedValue(point.change, null, ui.oneDecimal)})` : "")),
          ui.button({
            label: `Apply ${point.swaps}`, kind: "gold", disabled: locked, ariaLabel: `Apply ${title}: ${point.swaps} ${point.swaps === 1 ? "swap" : "swaps"}`,
            onClick: () => app.change({ op: "group", label: title, items: swaps.slice(0, point.swaps).map((s) => ({ op: "swap", cut: s.cut, add: s.add })), source: "suggested" }),
          }));
        const note = weakensNote(point);
        return note ? h("div", { class: "stack", style: { gap: "4px" } }, row, note) : row;
      }),
      h("p", { class: "muted small", text: "Each price point includes the smaller ones before it. Tap one to see its swaps." })));
    const point = points[chosen];
    const list = swaps.slice(0, point.swaps);
    const shown = suggest.showAll ? list : list.slice(0, SHOWN_SWAPS);
    out.push(h("section", {}, ui.sectionLabel(`${upTo(point)} · ${point.swaps} ${point.swaps === 1 ? "swap" : "swaps"}`, { tight: true }),
      shown.map((swap, i) => swapRow(app, deck, result, swap, i + 1, locked)),
      list.length > SHOWN_SWAPS ? h("button", {
        type: "button", class: "more", onclick: () => { suggest.showAll = !suggest.showAll; app.render(); },
      }, suggest.showAll ? "Show fewer" : `Show the other ${list.length - SHOWN_SWAPS}`) : null));
  }
  if (result.blocked.length) {
    out.push(h("section", {}, ui.sectionLabel(`Kept out by Bracket ${result.bracket}`, { tight: true }),
      result.blocked.map((entry) => h("p", { class: "para" }, h("b", { text: entry.card }), `: ${entry.reason}`))));
  }
  if (result.warnings.length) out.push(...result.warnings.map((text) => ui.banner({ tone: "warn", text })));
  return out;
}

/** The note under a price point that has brought the deck's answers to some kind of threat down from the starting
 *  list's count to what a typical deck at the bracket holds, or under it: "enchantments 7 → 4 (typical 4)". The server
 *  works the numbers out; the change in score is shown to one decimal, like the two scores beside it. */
function weakensNote(point: PricePoint): HTMLDivElement | null {
  if (!point.weakens || !point.weakens.length) return null;
  const kinds = point.weakens.map((w) => `${w.label} ${w.before} → ${w.after} (typical ${w.target})`).join(", ");
  return ui.banner({ tone: "warn", title: "Weakens interaction", children: [h("p", { text: kinds })] });
}

function swapRow(app: App, deck: ReadyDeck, result: SuggestAnswer, swap: Swap, n: number, locked: boolean): HTMLDivElement {
  const added = result.cards[swap.add] || { name: swap.add };
  const price = swap.owned ? "$0.00 · you own it" : swap.price === null || swap.price === undefined ? "price unknown" : ui.money(swap.price);
  return h("div", { class: "swap" },
    h("span", { class: "swap__n", text: String(n) }),
    h("a", { class: "swap__cards", href: app.link.card(deck.player, deck.id, swap.add), "aria-label": `${swap.cut} is replaced by ${added.name}. Open ${added.name}` },
      h("s", { text: swap.cut }), "→", h("b", { text: added.name })),
    ui.button({
      label: "Apply", kind: "outline", size: "small", disabled: locked, ariaLabel: `Swap ${swap.cut} for ${swap.add}`,
      onClick: () => app.change({ op: "swap", cut: swap.cut, add: swap.add, source: "suggested" }),
    }),
    h("span", { class: "swap__detail" }, h("b", { text: ui.signed(swap.gain) }), ` · ${price}`,
      swap.forced ? " · required" : "", swap.fills && swap.fills.length ? ` · fills ${swap.fills.join(", ")}` : ""));
}

function metricsTab(app: App, deck: ReadyDeck): HTMLDivElement {
  return metrics.metricsTab(app, deck);
}

// -------------------------------------------------------------------------------------------- banners for the deck

const SOURCE_NAMES: Record<string, string> = { edhrec: "EDHREC", edhtop16: "EDHTop16", spellbook: "Commander Spellbook", scryfall: "Scryfall", scryfall_tags: "Scryfall's card tags", archidekt: "Archidekt", mtgjson: "MTGJSON" };

/** Banners that describe the deck itself, worked out from the answer on every draw: they cannot go stale. */
function deckBanners(app: App, data: DeckAnswer): HTMLDivElement[] {
  const out: HTMLDivElement[] = [];
  const count = data.card_count;
  if (count !== 100) {
    const text = count === 101 ? "Cut one to get back to 100." : count === 99 ? "Add one to get to 100."
      : count > 100 ? "Cut cards to get back to 100." : "Add cards to get to 100.";
    out.push(ui.banner({ tone: "warn", title: `${count} cards.`, text }));
  }
  const head = data.metrics.headline;
  if (head.bracket_ok === false) {
    const item = metrics.findItem(data.metrics, "bracket");
    const changes = data.version.changes || [];
    const last = [...changes].reverse().find((c) => c.op !== "undo" && !c.undone);
    out.push(ui.banner({
      tone: "bad", title: `Breaks Bracket ${head.bracket}:`, text: (item && item.why.length ? item.why : ["the deck breaks a limit of this bracket."]).join(" "),
      actions: last ? [{ label: "Undo last change", onClick: () => app.undo(last.n) }] : [],
    }));
  }
  const stale = Object.entries(data.sources || {}).filter(([, info]) => info.cache === "stale");
  if (stale.length) {
    const name = ([source]: [string, ...unknown[]]) => SOURCE_NAMES[source] || source;
    const names = stale.length === 1 ? name(stale[0]) : `${stale.slice(0, -1).map(name).join(", ")} and ${name(stale[stale.length - 1])}`;
    const dates = stale.length === 1 ? ui.shortDate(stale[0][1].fetched) : stale.map(([source, info]) => `${name([source])} from ${ui.shortDate(info.fetched)}`).join(", ");
    out.push(ui.banner({ tone: "warn", text: `${names} didn't answer, so these numbers use ${stale.length === 1 ? "its" : "their"} data${stale.length === 1 ? ` from ${dates}` : ` (${dates})`}.` }));
  }
  const warnings = data.warnings || [];
  if (warnings.length) {
    const list = h("ul", { class: "problems" }, warnings.map((w) => h("li", { text: w })));
    out.push(ui.banner({ tone: "info", children: [h("details", {}, h("summary", { text: `${warnings.length} ${warnings.length === 1 ? "note" : "notes"} about these numbers` }), list)] }));
  }
  return out;
}

// ------------------------------------------------------------------------------------------------------- the screen

const TAB_LABELS: [Tab, string][] = [["cards", "Cards"], ["metrics", "Metrics"], ["changes", "Changes"], ["suggestions", "Suggestions"]];

function tabsNav(app: App, deck: ReadyDeck, tab: Tab): HTMLElement {
  return h("nav", { class: "tabs", "aria-label": "Deck sections" }, TAB_LABELS.map(([id, label]) => h("a", {
    href: app.link.deck(deck.player, deck.id, id), class: id === "suggestions" ? "tab--suggestions tab--wide" : `tab--${id}`,
    "aria-current": id === tab ? "page" : undefined, text: label,
  })));
}

function statLine(app: App, data: DeckAnswer): HTMLDivElement {
  const head = data.metrics.headline;
  const faded = app.saving ? "is-faded" : "";
  const score = metrics.findItem(data.metrics, "score");
  const removal = metrics.findItem(data.metrics, "removal_power");
  const swaps = changeCounts(data).added;
  const wide = app.state.wide;
  const ok = head.bracket_ok;
  const bracketMark = ok === true ? h("span", { class: "mark-ok" }, "✓", h("span", { class: "sr-only", text: " limits met" }))
    : ok === false ? h("span", { class: "mark-bad" }, "✗", h("span", { class: "sr-only", text: " limits broken" })) : null;
  return h("div", { class: "statline", role: "group", "aria-label": "The deck in numbers" },
    ui.stat({ value: ui.oneDecimal(head.score), label: "Score", mark: score ? ui.delta(score, { showBase: false, format: ui.oneDecimal }) : null, className: faded }),
    ui.stat({ value: head.bracket === null || head.bracket === undefined ? "—" : String(head.bracket), label: "Bracket", mark: bracketMark, tone: ok === false ? "bad" : "", className: faded }),
    ui.stat({ value: ui.oneDecimal(head.removal_power), label: "Removal", mark: removal ? ui.delta(removal, { showBase: false, format: ui.oneDecimal }) : null, className: faded }),
    ui.stat({ value: head.lands === null || head.lands === undefined ? "—" : String(head.lands), label: "Lands", className: `stat--lands ${faded}` }),
    ui.stat({ value: wide ? ui.money(head.price) : ui.moneyWhole(head.price), label: wide && swaps !== null ? `Spent · ${swapWord(swaps)}` : "Spent", className: faded }));
}

function hero(app: App, deck: ReadyDeck): HTMLElement {
  const data = deck.data;
  const { version, commanders } = data;
  const colors = ui.colorsOf(commanders);
  const bracket = data.spec && data.spec.bracket;
  const budget = version.settings.budget;
  const words = ([] as string[]).concat(data.spec.themes || [], data.spec.playstyle ? [data.spec.playstyle] : []);
  const nameParts = version.name.trim().split(/\s+/);
  const last = nameParts.pop();
  const tiles = commanders.map((card) => ui.cardTile(card, { href: app.link.card(deck.player, deck.id, card.name), focusKey: `card:${card.name}`, lazy: false }));
  const meta = (extra?: string) => [ui.colorLetters(colors), bracket ? ` · Bracket ${bracket}` : "", budget !== undefined && budget !== null ? ` · Budget ${ui.dollars(budget)}` : "", extra];
  return h("section", { class: "hero", "aria-label": "Commander" },
    tiles,
    h("div", { class: "hero__info" },
      h("div", { class: "hero__name", text: commanders.map((c) => c.name).join(" & ") }),
      h("h1", { class: "hero__h1" }, nameParts.length ? `${nameParts.join(" ")} ` : "", h("span", { class: "accent", text: last })),
      h("div", { class: "hero__meta" }, meta()),
      h("div", { class: "hero__sub" }, `${commanders.map((c) => c.name).join(" & ")} · `, meta(words.length ? ` · ${words.join(", ")}` : "")),
      h("div", { class: "tags hero__tags" }, words.map((w) => ui.tag(w, { on: true })))));
}

function phoneTopbar(app: App, deck: ReadyDeck, title: string, sub: string, { adding }: { adding: boolean }): HTMLDivElement {
  return h("div", { class: "topbar__row" },
    ui.iconButton({ icon: "back", label: "Back to decks", href: app.link.decks }),
    h("div", { class: "topbar__title" }, h("h1", { class: "topbar__name", text: title }), h("div", { class: "topbar__sub", text: sub })),
    app.saving ? h("span", { class: "topbar__saving", role: "status", text: "Saving…" }) : null,
    adding ? ui.button({ label: "Add", kind: "primary", icon: "plus", href: app.link.add(deck.player, deck.id), focusKey: "add" }) : null);
}

function wideTopbar(app: App, deck: ReadyDeck, data: DeckAnswer, tab: Tab): HTMLDivElement {
  const search = tab === "cards" ? deckSearch(cardsState(deck)).el : null;
  return h("div", { class: "topbar__row" },
    h("a", { class: "brand", href: app.link.decks }, ui.pip(), "Commander decks"),
    h("nav", { class: "crumbs", "aria-label": "Breadcrumb" },
      h("a", { class: "crumb", href: app.link.decks, text: deck.player }), h("span", { "aria-hidden": "true", text: "›" }),
      h("a", { class: "crumb", href: app.link.decks, text: data.base.name }), h("span", { "aria-hidden": "true", text: "›" }),
      h("span", { text: data.version.name })),
    h("span", { class: "topbar__spacer" }),
    app.saving ? h("span", { class: "topbar__saving", role: "status", text: "Saving…" }) : null,
    search,
    ui.button({ label: "Add a card", kind: "primary", icon: "plus", href: app.link.add(deck.player, deck.id), focusKey: "add" }));
}

/** The whole screen for the open deck, whatever state it is in: {title, topbar, main}. */
export function view(app: App): Screen {
  const { state } = app;
  const deck = state.deck;
  const route = state.route;
  const tab = (route.name === "deck" && route.tab) || state.lastTab;
  if (!deck) return plain(app, "Opening the deck…", ui.working("Opening the deck…"));
  if (deck.status === "error") return failed(app, deck);
  if (!deck.data) {
    if (deck.status === "preparing") return plain(app, deck.id, ui.waitingBanner(deck.progress));
    return plain(app, deck.id, ui.working("Opening the deck…"));
  }
  const ready = deck as ReadyDeck;
  const data = ready.data;
  const wide = state.wide;
  const topbar = wide ? wideTopbar(app, ready, data, tab) : phoneTopbar(app, ready, data.version.name, `${deck.player} · from ${data.base.name}`, { adding: true });
  const body = tab === "metrics" ? metricsTab(app, ready) : tab === "changes" ? changesTab(app, ready) : tab === "suggestions" ? suggestionsTab(app, ready) : cardsTab(app, ready);
  const notices = deckBanners(app, data);
  const mainColumn = h("div", { class: "deck-main" }, tabsNav(app, ready, tab), notices.length ? h("div", { class: "notices" }, notices) : null, h("div", { class: "deckbody" }, body));
  const columns = h("div", { class: wide && tab !== "metrics" ? "deck-columns" : "deck-columns deck-columns--single" }, mainColumn);
  if (wide && tab !== "metrics") columns.append(metrics.aside(app, ready));
  const main = h("div", { class: "page page--deck" }, hero(app, ready), statLine(app, data), columns);
  return { title: data.version.name, topbar, main };
}

function plain(app: App, title: string, content: HTMLElement): Screen {
  return {
    title,
    topbar: h("div", { class: "topbar__row" }, ui.iconButton({ icon: "back", label: "Back to decks", href: app.link.decks }),
      h("div", { class: "topbar__title" }, h("h1", { class: "topbar__name", text: title }))),
    main: h("div", { class: "page" }, content),
  };
}

function failed(app: App, deck: DeckState): Screen {
  const error = deck.error!;
  let content;
  if (error.kind === "not_found") {
    content = ui.emptyState({
      title: "That deck isn't here", text: error.message,
      action: ui.button({ label: "Back to your decks", kind: "primary", href: app.link.decks }),
    });
  } else {
    content = ui.failureBanner(error, { retry: () => app.loadDeck({ fresh: true }) });
  }
  return plain(app, deck.id, content);
}
